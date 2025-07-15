# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
# grader_s/grader_s/handlers
import datetime
import json
import os.path
import shutil
import subprocess
from http import HTTPStatus
from typing import List

import isodate
import pandas as pd
import tornado
from celery import chain
from sqlalchemy import label
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import func
from tornado.web import HTTPError

from grader_service.api.models.submission import Submission as SubmissionModel
from grader_service.autograding.celery.tasks import (
    autograde_task,
    generate_feedback_task,
    lti_sync_task,
)
from grader_service.convert.gradebook.models import GradeBookModel
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.handlers.handler_utils import GitRepoType, parse_ids
from grader_service.orm.assignment import Assignment
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import Lecture
from grader_service.orm.submission import Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Role, Scope
from grader_service.plugins.lti import LTISyncGrades
from grader_service.registry import VersionSpecifier, register_handler


def remove_points_from_submission(submissions):
    for s in submissions:
        if s.feedback_status not in ("generated", "feedback_outdated"):
            s.score = None
    return submissions


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/submissions\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionLectureHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /lectures/{lecture_id}/submissions.
    """

    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int):
        """Return the submissions of a specific lecture.

        Two query parameter:
        1 - filter
            latest: only get the latest submissions of users.
            best: only get the best submissions by score of users.
        2 - format:
            csv: return list as comma separated values
            json: return list as JSON

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :raises HTTPError: throws err if user is not authorized or
        the assignment was not found
        """
        lecture_id = parse_ids(lecture_id)
        self.validate_parameters("filter", "format")
        submission_filter = self.get_argument("filter", "best")
        if submission_filter not in ["latest", "best"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="Filter parameter \
            has to be either 'latest' or 'best'",
            )
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="Response format \
            can either be 'json' or 'csv'",
            )

        role: Role = self.get_role(lecture_id)
        if role.role < Scope.tutor:
            raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")

        if submission_filter == "latest":
            subquery = (
                self.session.query(Submission.username, func.max(Submission.date).label("max_date"))
                .join(Assignment, Submission.assignid == Assignment.id)
                .filter(Assignment.lectid == lecture_id)
                .filter(Submission.deleted == DeleteState.active)
                .group_by(Submission.username, Assignment.id)
                .subquery()
            )
        else:
            subquery = (
                self.session.query(
                    Submission.username, func.max(Submission.score).label("max_score")
                )
                .join(Assignment, Submission.assignid == Assignment.id)
                .filter(Assignment.lectid == lecture_id)
                .filter(Submission.deleted == DeleteState.active)
                .group_by(Submission.username, Assignment.id)
                .subquery()
            )

        submissions_query = (
            self.session.query(
                label("username", Submission.username),
                label("score", Submission.score),
                label("assignment", Assignment.name),
            )
            .join(Assignment, Submission.assignid == Assignment.id)
            .filter(Assignment.lectid == lecture_id)
            .filter(Submission.deleted == DeleteState.active)
        )

        if submission_filter == "latest":
            submissions = (
                submissions_query.join(
                    subquery,
                    (Submission.username == subquery.c.username)
                    & (Submission.date == subquery.c.max_date),
                )
                .order_by(Assignment.id)
                .all()
            )
        else:
            submissions = (
                submissions_query.join(
                    subquery,
                    (Submission.username == subquery.c.username)
                    & (Submission.score == subquery.c.max_score),
                )
                .order_by(Submission.id)
                .all()
            )

        df = pd.DataFrame(submissions, columns=["Username", "Score", "Assignment"])
        pivoted_df = df.pivot_table(
            values="Score", index="Username", columns="Assignment", aggfunc="first", dropna=False
        ).fillna("-")

        if response_format == "csv":
            self.set_header("Content-Type", "text/csv")
            self.write(pivoted_df.to_csv(header=True, index=True))
        else:
            self.set_header("Content-Type", "application/json")
            self.write(pivoted_df.to_json(orient="columns", force_ascii=False))


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments"
    + r"\/(?P<assignment_id>\d*)\/submissions\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions.
    """

    def on_finish(self):
        # we do not close the session we just commit because we might run
        # LocalAutogradeExecutor or GenerateFeedbackExecutor in POST which
        # still need it
        pass

    def validate_assignment(self, lecture_id, assignment_id):
        """Checks if assignment is part of lecture

        Args:
            lecture_id (int): lecture id
            assignment_id (int): assignment id

        Raises:
            HTTPError: raises 404 error if no assignment in lecture is found
        """
        try:
            # Query the Assignment table to check if the assignment exists and is linked to the correct lecture
            self.session.query(Assignment).filter_by(id=assignment_id, lectid=lecture_id).one()
        except NoResultFound:
            # Raise an error if no such assignment exists for the provided lecture
            raise HTTPError(
                HTTPStatus.NOT_FOUND,
                reason=f"Assignment {assignment_id} does not exist for lecture {lecture_id}",
            )
        return True

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """Return the submissions of an assignment.

        Two query parameter: latest, instructor-version.

        latest: only get the latest submissions of users.
        instructor-version: if true, get the submissions of all users in
        lecture if false, get own submissions.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if user is not authorized or
        the assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters("filter", "instructor-version", "format")
        submission_filter = self.get_argument("filter", "none")
        if submission_filter not in ["none", "latest", "best"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="Filter parameter \
            has to be either 'none', 'latest' or 'best'",
            )
        instr_version = self.get_argument("instructor-version", None) == "true"
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="Response format \
            can either be 'json' or 'csv'",
            )

        # check required scopes for instructor version
        role: Role = self.get_role(lecture_id)
        if instr_version and role.role < Scope.tutor:
            raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")
        # validate that assignment is part of lecture
        self.validate_assignment(lecture_id, assignment_id)

        # get list of submissions based on arguments
        username = None if instr_version else role.username
        if submission_filter == "latest":
            submissions = self.get_latest_submissions(assignment_id, username=username)
        elif submission_filter == "best":
            submissions = self.get_best_submissions(assignment_id, username=username)
        else:
            query = self.session.query(Submission).filter(
                Submission.assignid == assignment_id, Submission.deleted == DeleteState.active
            )
            if username:
                query = query.filter(Submission.username == username)
            submissions = query.order_by(Submission.id).all()

        if response_format == "csv":
            self.set_header("Content-Type", "text/csv")
            for i, s in enumerate(submissions):
                d = s.model.to_dict()
                if i == 0:
                    self.write(",".join((k for k in d.keys() if k != "logs")) + "\n")
                self.write(",".join((str(v) for k, v in d.items() if k != "logs")) + "\n")
        else:
            if not instr_version:
                submissions = remove_points_from_submission(submissions)

            self.write_json(submissions)
        self.session.close()

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def post(self, lecture_id: int, assignment_id: int):
        """Create submission based on commit hash.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if user is not authorized or
        the assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        try:
            commit_hash = body["commit_hash"]
        except KeyError:
            raise HTTPError(400, reason="Commit hash not found in body")

        role = self.get_role(lecture_id)
        lecture = self.get_lecture(lecture_id)
        assignment = self.get_assignment(lecture_id, assignment_id)
        if assignment.status == "complete":
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot submit completed assignment!")
        if role.role == Scope.student and assignment.status != "released":
            raise HTTPError(HTTPStatus.NOT_FOUND)
        # set utc time
        submission_ts = datetime.datetime.now(datetime.timezone.utc)
        # use implicit utc time to compare with database objects
        # submission_ts = submission_ts.replace(tzinfo=None)

        score_scaling = 1.0
        if assignment.settings.deadline is not None:
            score_scaling = self.calculate_late_submission_scaling(assignment, submission_ts, role)

        if assignment.settings.max_submissions:
            submissions = assignment.submissions
            usersubmissions = [s for s in submissions if s.username == role.username]
            if (
                len(usersubmissions) >= assignment.settings.max_submissions
                and role.role < Scope.tutor
            ):
                raise HTTPError(
                    HTTPStatus.CONFLICT, reason="Maximum number of submissions reached!"
                )

        submission = Submission()
        submission.assignid = assignment.id
        submission.date = submission_ts
        submission.username = self.user.name
        submission.score_scaling = score_scaling

        git_repo_path = self.construct_git_dir(
            repo_type=GitRepoType.USER, lecture=assignment.lecture, assignment=assignment
        )

        try:
            # Commit hash "0"*40 is used to differentiate between submissions created by
            # instructors for students and normal submissions by any user.
            # In this case submissions for the student might not exist, so we cannot reference
            # a non-existing commit_hash. When submission is set to edited, autograder uses edit
            # repository, so we don't need the commit_hash of the submission.
            if commit_hash != "0" * 40:
                if not os.path.exists(git_repo_path):
                    raise HTTPError(
                        HTTPStatus.UNPROCESSABLE_ENTITY, reason="User git repository not found"
                    )
                subprocess.run(
                    ["git", "branch", "main", "--contains", commit_hash],
                    cwd=git_repo_path,
                    capture_output=True,
                )
        except subprocess.CalledProcessError:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Commit not found")

        submission.commit_hash = commit_hash
        submission.auto_status = "not_graded"
        submission.manual_status = "not_graded"
        submission.feedback_status = "not_generated"

        automatic_grading = assignment.settings.autograde_type

        self.session.add(submission)
        self.session.commit()
        self.set_status(HTTPStatus.CREATED)
        self.write_json(submission)

        # If the assignment has automatic grading or fully
        # automatic grading perform necessary operations
        if automatic_grading in ["auto", "full_auto"]:
            submission.auto_status = "pending"
            self.session.commit()
            self.set_status(HTTPStatus.ACCEPTED)

            if automatic_grading == "full_auto":
                submission.feedback_status = "generating"
                self.session.commit()

                # use immutable signature: https://docs.celeryq.dev/en/stable/reference/celery.app.task.html#celery.app.task.Task.si
                grading_chain = chain(
                    autograde_task.si(lecture_id, assignment_id, submission.id),
                    generate_feedback_task.si(lecture_id, assignment_id, submission.id),
                    lti_sync_task.si(
                        lecture.serialize(),
                        assignment.serialize(),
                        [submission.serialize()],
                        feedback_sync=True,
                    ),
                )
            else:
                grading_chain = chain(autograde_task.si(lecture_id, assignment_id, submission.id))
            grading_chain()

        if automatic_grading == "unassisted":
            self.session.close()

    @staticmethod
    def calculate_late_submission_scaling(
        assignment: Assignment, submission_ts, role: Role
    ) -> float:
        # make submission timestamp timezone aware
        deadline = assignment.settings.deadline
        if submission_ts.tzinfo is None:
            submission_ts = submission_ts.replace(tzinfo=datetime.timezone.utc)
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=datetime.timezone.utc)

        if assignment.settings.late_submission and len(assignment.settings.late_submission) > 0:
            scaling = 0.0
            if submission_ts <= deadline:
                scaling = 1.0
            else:
                for period in assignment.settings.late_submission:
                    late_submission_date = deadline + isodate.parse_duration(period.period)
                    if submission_ts < late_submission_date:
                        scaling = period.scaling
                        break
                if scaling == 0.0 and role.role < Scope.tutor:
                    raise HTTPError(
                        HTTPStatus.CONFLICT,
                        reason="Submission after last late submission period of assignment!",
                    )
        else:
            if submission_ts < deadline:
                scaling = 1.0
            else:
                if role.role < Scope.tutor:
                    raise HTTPError(
                        HTTPStatus.CONFLICT, reason="Submission after due date of assignment!"
                    )
                else:
                    scaling = 0.0
        return scaling


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/"
    + r"(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionObjectHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions
    /{submission_id}.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Returns a specific submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        submission = self.get_submission(lecture_id, assignment_id, submission_id)
        if (
            self.get_role(lecture_id).role == Scope.student
            and submission.username != self.user.name
        ):
            raise HTTPError(HTTPStatus.NOT_FOUND)
        self.write_json(submission)

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Updates a specific submission and returns the updated entity.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        body = tornado.escape.json_decode(self.request.body)
        sub_model = SubmissionModel.from_dict(body)
        sub = self.get_submission(lecture_id, assignment_id, submission_id)
        # sub.date = sub_model.submitted_at
        # sub.assignid = assignment_id

        role = self.get_role(lecture_id)
        if role.role >= Scope.instructor:
            sub.username = sub_model.username
        sub.auto_status = sub_model.auto_status
        sub.manual_status = sub_model.manual_status
        sub.edited = sub_model.edited
        sub.feedback_status = sub_model.feedback_status
        if sub_model.score_scaling is not None and sub.score_scaling != sub_model.score_scaling:
            sub.score_scaling = sub_model.score_scaling
            if sub.grading_score is not None:
                # recalculate score based on new scaling factor
                sub.score = sub_model.score_scaling * sub.grading_score
        self.session.commit()
        self.write_json(sub)

    def delete(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Soft-Deletes a specific submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: if submission can't be deleted due to it having feedback
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        self.validate_parameters()
        submission = self.get_submission(lecture_id, assignment_id, submission_id)

        if submission is not None:
            if submission.feedback_status != "not_generated":
                raise HTTPError(
                    HTTPStatus.FORBIDDEN, reason="Only submissions without feedback can be deleted."
                )
            # if assignment has deadline
            if submission.assignment.settings.deadline:
                # if assignment's deadline has passed
                if submission.assignment.settings.deadline < datetime.datetime.now(
                    datetime.timezone.utc
                ):
                    raise HTTPError(
                        HTTPStatus.FORBIDDEN,
                        reason="Submission can't be deleted, due date of assigment has passed.",
                    )
            else:
                previously_deleted = (
                    self.session.query(Submission)
                    .filter(
                        Submission.id == submission_id,
                        Submission.assignid == assignment_id,
                        Submission.deleted == DeleteState.deleted,
                    )
                    .one_or_none()
                )
                if previously_deleted is not None:
                    self.session.delete(previously_deleted)
                    self.session.commit()

                submission.deleted = DeleteState.deleted
                self.session.commit()
        else:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Submission to delete not found.")


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/"
    + r"(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/logs\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionLogsHandler(GraderBaseHandler):
    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Returns logs of a submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: throws err if the submission logs are not found
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        logs = self.session.query(SubmissionLogs).get(submission_id)
        if logs is not None:
            self.write_json(logs.logs)
        else:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Properties of submission were not found")


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/"
    + r"(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/"
    + r"properties\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionPropertiesHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/submissions/
    {submission_id}/properties.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Returns the properties of a submission,

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: throws err if the submission or
        their properties are not found
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        properties = self.session.get(SubmissionProperties, submission_id)
        if properties is not None and properties.properties is not None:
            # delete source cells from properties if user is student
            if self.get_role(lecture_id).role == Scope.student:
                model = GradeBookModel.from_dict(json.loads(properties.properties))
                for notebook in model.notebooks.values():
                    notebook.source_cells_dict = {}
                self.write(json.dumps(model.to_dict()))
            else:
                self.write(properties.properties)
        else:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Properties of submission were not found")

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Updates the properties of a submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: throws err if the submission are not found
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        submission = self.get_submission(lecture_id, assignment_id, submission_id)
        properties_string: str = self.request.body.decode("utf-8")

        try:
            gradebook = GradeBookModel.from_dict(json.loads(properties_string))

            score = gradebook.score
            submission.grading_score = score
            submission.score = submission.score_scaling * score

        except Exception as e:
            self.log.info(e)
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot parse properties file!")

        properties = SubmissionProperties(properties=properties_string, sub_id=submission.id)

        self.session.merge(properties)

        if submission.feedback_status == "generated":
            submission.feedback_status = "feedback_outdated"

        if submission.manual_status == "manually_graded":
            submission.manually_graded = "being_edited"

        self.session.commit()
        self.write_json(submission)

    # TODO: not used, remove?
    def get_extra_credit(self, gradebook):
        extra_credit = 0
        for notebook in gradebook.notebooks.values():
            for grades in notebook.grades:
                extra_credit += grades.extra_credit if grades.extra_credit is not None else 0
        self.log.info("Extra credit is " + str(extra_credit))
        return extra_credit


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/"
    + r"(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/edit\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionEditHandler(GraderBaseHandler):
    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Create or overwrites the repository which stores changes of
        submissions files
        :param lecture_id: lecture id
        :param assignment_id: assignment id
        :param submission_id: submission id
        :return:
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()

        submission = self.get_submission(lecture_id, assignment_id, submission_id)
        assignment = submission.assignment
        lecture = assignment.lecture

        # Path to repository which will store edited submission files
        git_repo_path = os.path.join(
            self.gitbase, lecture.code, str(assignment.id), "edit", str(submission_id)
        )

        # Path to repository of student which contains the submitted files
        submission_repo_path = os.path.join(
            self.gitbase, lecture.code, str(assignment.id), "user", submission.username
        )

        if os.path.exists(git_repo_path):
            shutil.rmtree(git_repo_path)

        # Creating bare repository
        if not os.path.exists(git_repo_path):
            os.makedirs(git_repo_path, exist_ok=True)

        await self._run_command_async("git init --bare", git_repo_path)

        # Create temporary paths to copy the submission
        # files in the edit repository
        tmp_path = os.path.join(
            self.application.grader_service_dir,
            "tmp",
            lecture.code,
            str(assignment.id),
            "edit",
            str(submission.id),
        )

        tmp_input_path = os.path.join(tmp_path, "input")

        tmp_output_path = os.path.join(tmp_path, "output")

        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path, ignore_errors=True)

        os.makedirs(tmp_input_path, exist_ok=True)

        # Init local repository
        command = "git init"
        await self._run_command_async(command, tmp_input_path)

        # Pull user repository
        command = f'git pull "{submission_repo_path}" main'
        await self._run_command_async(command, tmp_input_path)
        self.log.info("Successfully cloned repo")

        # Checkout to correct submission commit
        command = f"git checkout {submission.commit_hash}"
        await self._run_command_async(command, tmp_input_path)
        self.log.info(f"Now at commit {submission.commit_hash}")

        # Copy files to output directory
        shutil.copytree(tmp_input_path, tmp_output_path, ignore=shutil.ignore_patterns(".git"))

        # Init local repository
        command = "git init"
        await self._run_command_async(command, tmp_output_path)

        # Add edit remote
        command = f"git remote add edit {git_repo_path}"
        await self._run_command_async(command, tmp_output_path)
        self.log.info("Successfully added edit remote")

        # Switch to main
        command = "git switch -c main"
        await self._run_command_async(command, tmp_output_path)
        self.log.info("Successfully switched to branch main")

        # Add files to staging
        command = "git add -A"
        await self._run_command_async(command, tmp_output_path)
        self.log.info("Successfully added files to staging")

        # Commit Files
        command = 'git commit -m "Initial commit" '
        await self._run_command_async(command, tmp_output_path)
        self.log.info("Successfully commited files")

        # Push copied files
        command = "git push edit main"
        await self._run_command_async(command, tmp_output_path)
        self.log.info("Successfully pushed copied files")

        submission.edited = True
        self.session.commit()
        self.write_json(submission)


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/lti\/?",
    version_specifier=VersionSpecifier.ALL,
)
class LtiSyncHandler(GraderBaseHandler):
    cache_token = {"token": None, "ttl": datetime.datetime.now()}

    @authorize([Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int):
        """Starts the LTI sync process (if enabled).
        Request can have an optional parameter 'option'.
        if 'option' == 'latest': sync all latest submissions with feedback
           'option' == 'best': sync all best submissions with feedback
           'option' == 'selection': sync all submissions in body (default, if no param is set)

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters("option")
        lti_option = self.get_argument("option", "latest")

        assignment: Assignment = self.session.get(Assignment, assignment_id)
        if (
            (assignment is None)
            or (assignment.deleted == DeleteState.deleted)
            or (int(assignment.lectid) != int(lecture_id))
        ):
            self.log.error("Assignment with id " + str(assignment_id) + " was not found")
            return None
        lecture: Lecture = assignment.lecture

        # get all latest submissions with feedback
        if lti_option == "latest":
            submissions = self.get_latest_submissions(assignment_id, must_have_feedback=True)
        # get all best submissions with feedback
        elif lti_option == "best":
            submissions = self.get_best_submissions(assignment_id, must_have_feedback=True)
        else:
            # get submissions with given submission ids
            try:
                body = tornado.escape.json_decode(self.request.body)
                submission_ids: List[int] = body.get("submission_ids", [])

                if not submission_ids:
                    raise ValueError("No submission IDs provided")

                # Fetch and validate submissions
                submissions = (
                    self.session.query(Submission)
                    .filter(
                        Submission.id.in_(submission_ids),
                        Submission.auto_status == "automatically_graded",
                        Submission.assignid == assignment_id,
                    )
                    .all()
                )
                if len(submissions) != len(submission_ids):
                    raise HTTPError(
                        HTTPStatus.BAD_REQUEST,
                        reason="Some submission IDs are invalid or do not belong to this assignment.",
                    )

            except Exception as e:
                err_msg = f"Could not process submission IDs: {e}"
                self.log.error(err_msg)
                raise HTTPError(HTTPStatus.BAD_REQUEST, reason=err_msg)

        lti_plugin = LTISyncGrades.instance()
        lecture_model = lecture.serialize()
        assignment_model = assignment.serialize()
        submissions_model = [sub.serialize() for sub in submissions if isinstance(sub, Submission)]
        # check if the lti plugin is enabled
        if lti_plugin.check_if_lti_enabled(
            lecture_model, assignment_model, submissions_model, feedback_sync=False
        ):
            try:
                results = await lti_plugin.start(lecture_model, assignment_model, submissions_model)
                return self.write_json(results)
            except HTTPError as e:
                err_msg = f"Could not sync grades: {e.reason}"
                self.log.info(err_msg)
                raise HTTPError(HTTPStatus.INTERNAL_SERVER_ERROR, reason=err_msg)
            except Exception as e:
                self.log.error("Could not sync grades: " + str(e))
                raise HTTPError(500, reason="An unexpected error occured.")
        else:
            raise HTTPError(403, reason="LTI plugin is not enabled by administator.")


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/count\/?"
)
class SubmissionCountHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/count.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """Returns the count of submissions made by the student for an assignment, no matter if submission
         was deleted or not.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)

        role = self.get_role(lecture_id)

        usersubmissions_count = (
            self.session.query(Submission)
            .filter(Submission.assignid == assignment_id, Submission.username == role.username)
            .count()
        )

        self.write_json({"submission_count": usersubmissions_count})
        self.session.close()
