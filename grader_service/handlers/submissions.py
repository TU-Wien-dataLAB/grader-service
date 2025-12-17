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
from sqlalchemy.orm.exc import NoResultFound, ObjectDeletedError
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
from grader_service.orm.submission import AutoStatus, FeedbackStatus, ManualStatus, Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Role, Scope
from grader_service.orm.user import User
from grader_service.plugins.lti import LTISyncGrades
from grader_service.registry import VersionSpecifier, register_handler

# Commit hash is used to differentiate between submissions created by instructors for students and
# normal submissions by any user.
INSTRUCTOR_SUBMISSION_COMMIT_CASH = "0" * 40


def remove_points_from_submission(submissions):
    for s in submissions:
        if s.feedback_status not in (FeedbackStatus.GENERATED, FeedbackStatus.FEEDBACK_OUTDATED):
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

    @authorize([Scope.tutor, Scope.instructor, Scope.admin])
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
                reason="Filter parameter has to be either 'latest' or 'best'",
            )
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, reason="Response format can either be 'json' or 'csv'"
            )

        if submission_filter == "latest":
            query = (
                self.session.query(Submission.user_id, func.max(Submission.date).label("max_date"))
                .join(Assignment, Submission.assignid == Assignment.id)
                .filter(Assignment.lectid == lecture_id)
                .group_by(Submission.user_id, Assignment.id)
            )
        else:
            query = (
                self.session.query(
                    Submission.user_id, func.max(Submission.score).label("max_score")
                )
                .join(Assignment, Submission.assignid == Assignment.id)
                .filter(Assignment.lectid == lecture_id)
                .group_by(Submission.user_id, Assignment.id)
            )

        if not self.user.is_admin:
            query = query.filter(Submission.deleted == DeleteState.active)

        subquery = query.subquery()

        submissions_query = (
            self.session.query(
                label("username", User.name),
                label("score", Submission.score),
                label("assignment", Assignment.name),
            )
            .join(Assignment, Submission.assignid == Assignment.id)
            .join(User, Submission.user_id == User.id)
            .filter(Assignment.lectid == lecture_id)
        )

        if not self.user.is_admin:
            submissions_query = submissions_query.filter(Submission.deleted == DeleteState.active)

        if submission_filter == "latest":
            submissions = (
                submissions_query.join(
                    subquery,
                    (Submission.user_id == subquery.c.user_id)
                    & (Submission.date == subquery.c.max_date),
                )
                .order_by(Assignment.id)
                .all()
            )
        else:
            submissions = (
                submissions_query.join(
                    subquery,
                    (Submission.user_id == subquery.c.user_id)
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
    path=r"\/api\/users\/(?P<username>[^\/]+)\/submissions\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionUserHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /users/{username}/submissions.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def get(self, username: str):
        """Return the submissions of a specific user.

        One query parameter:
        1 - format:
            csv: return list as comma separated values
            json: return list as JSON

        :param username: name of the user
        :type username: str
        :raises HTTPError: throws err if user is not authorized
        """
        self.validate_parameters("format")
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, reason="Response format can either be 'json' or 'csv'"
            )

        if not self.user.is_admin:
            if username != self.user.name:
                raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")

        db_user = self.session.query(User).filter_by(name=username).first()
        if db_user is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="User not found")

        submissions_query = (
            self.session.query(Submission)
            .filter(Submission.user_id == db_user.id)
            .order_by(Submission.id)
        )

        if not self.user.is_admin:
            submissions_query = submissions_query.filter(Submission.deleted == DeleteState.active)

        submissions = submissions_query.all()

        if response_format == "csv":
            self._write_csv(submissions)
        else:
            self.write_json([s.serialize_with_lectid() for s in submissions])
        self.session.close()

    def _write_csv(self, submissions):
        self.set_header("Content-Type", "text/csv")
        for i, s in enumerate(submissions):
            d = s.serialize_with_lectid()
            if i == 0:
                self.write(",".join((k for k in d.keys() if k != "logs")) + "\n")
            self.write(",".join((str(v) for k, v in d.items() if k != "logs")) + "\n")


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
        # LocalAutogradeExecutor or LocalFeedbackExecutor in POST which
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

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
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
                reason="Filter parameter has to be either 'none', 'latest' or 'best'",
            )
        instr_version = self.get_argument("instructor-version", None) == "true"
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, reason="Response format can either be 'json' or 'csv'"
            )

        if not self.user.is_admin:
            # check required scopes for instructor version
            role: Role = self.get_role(lecture_id)
            if instr_version and role.role < Scope.tutor:
                raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")
        # validate that assignment is part of lecture
        self.validate_assignment(lecture_id, assignment_id)

        # get list of submissions based on arguments
        user_id = None if instr_version else self.user.id

        if submission_filter == "latest":
            submissions = self.get_latest_submissions(assignment_id, user_id=user_id)
        elif submission_filter == "best":
            submissions = self.get_best_submissions(assignment_id, user_id=user_id)
        else:
            if self.user.is_admin:
                query = self.session.query(Submission).filter(Submission.assignid == assignment_id)
            else:
                query = self.session.query(Submission).filter(
                    Submission.assignid == assignment_id, Submission.deleted == DeleteState.active
                )

            if user_id:
                query = query.filter(Submission.user_id == user_id)
            submissions = query.order_by(Submission.id).all()

        if response_format == "csv":
            self._write_csv(submissions)
        else:
            if not instr_version:
                submissions = remove_points_from_submission(submissions)

            self.write_json(submissions)
        self.session.close()

    def _write_csv(self, submissions):
        self.set_header("Content-Type", "text/csv")
        for i, s in enumerate(submissions):
            d = s.model.to_dict()
            if i == 0:
                self.write(",".join((k for k in d.keys() if k != "logs")) + "\n")
            self.write(",".join((str(v) for k, v in d.items() if k != "logs")) + "\n")

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
            raise HTTPError(HTTPStatus.NOT_FOUND, "Assignment not found")
        # set utc time
        submission_ts = datetime.datetime.now(datetime.timezone.utc)
        # use implicit utc time to compare with database objects
        # submission_ts = submission_ts.replace(tzinfo=None)

        score_scaling = 1.0
        if assignment.settings.deadline is not None:
            score_scaling = self.calculate_late_submission_scaling(assignment, submission_ts, role)

        if assignment.settings.max_submissions and role.role < Scope.tutor:
            submissions = assignment.submissions
            user_submissions = [s for s in submissions if s.user_id == role.user_id]
            if len(user_submissions) >= assignment.settings.max_submissions:
                raise HTTPError(
                    HTTPStatus.CONFLICT, reason="Maximum number of submissions reached!"
                )

        submission = Submission()
        submission.assignid = assignment.id
        submission.date = submission_ts
        submission.score_scaling = score_scaling

        username = body.get("username")
        if username is not None and role.role >= Scope.tutor:
            # Instructor/tutor creates a submission for a student:
            s_user = self.session.query(User).filter(User.name == username).one_or_none()
            if s_user is None:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason=f"User {username} not found")
            s_user_role = self.session.get(Role, (s_user.id, lecture_id))
            if s_user_role is None:
                raise HTTPError(
                    HTTPStatus.NOT_FOUND,
                    reason=f"User {username} does not take part in this lecture",
                )
            submission.user_id = s_user.id
        else:
            # A user creates a submission for themselves.
            submission.user_id = self.user.id

            git_repo_path = self.construct_git_dir(
                repo_type=GitRepoType.USER, lecture=assignment.lecture, assignment=assignment
            )

            # If no submissions for the student exists, we cannot reference a non-existing
            # commit_hash.
            if not os.path.exists(git_repo_path):
                raise HTTPError(
                    HTTPStatus.UNPROCESSABLE_ENTITY, reason="User git repository not found"
                )
            try:
                subprocess.run(
                    ["git", "branch", "main", "--contains", commit_hash],
                    cwd=git_repo_path,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Commit not found")

        submission.commit_hash = commit_hash
        submission.auto_status = AutoStatus.NOT_GRADED
        submission.manual_status = ManualStatus.NOT_GRADED
        submission.feedback_status = FeedbackStatus.NOT_GENERATED

        automatic_grading = assignment.settings.autograde_type

        self.session.add(submission)
        self.session.commit()
        self.set_status(HTTPStatus.CREATED)
        self.write_json(submission)

        # If the assignment has automatic or fully automatic grading, run the necessary tasks.
        # The autograding is not performed when an instructor creates a new submission for a student.
        # Note: A specific commit hash is used to differentiate between submissions created by
        # instructors for students and normal submissions by any user.
        if (
            automatic_grading in ["auto", "full_auto"]
            and commit_hash != INSTRUCTOR_SUBMISSION_COMMIT_CASH
        ):
            submission.auto_status = AutoStatus.PENDING
            self.session.commit()
            self.set_status(HTTPStatus.ACCEPTED)

            if automatic_grading == "full_auto":
                submission.feedback_status = FeedbackStatus.GENERATING
                self.session.commit()

                # use immutable signature:
                # https://docs.celeryq.dev/en/stable/reference/celery.app.task.html#celery.app.task.Task.si
                grading_chain = chain(
                    autograde_task.si(lecture_id, assignment_id, submission.id),
                    generate_feedback_task.si(lecture_id, assignment_id, submission.id),
                    lti_sync_task.si(
                        lecture.serialize(),
                        assignment.serialize(),
                        [submission.serialize_with_user()],
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

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
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
            not self.user.is_admin
            and self.get_role(lecture_id).role == Scope.student
            and submission.user_id != self.user.id
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
            sub.user_id = sub_model.user_id
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

    @authorize([Scope.student, Scope.tutor, Scope.instructor, Scope.admin])
    async def delete(self, lecture_id: int, assignment_id: int, submission_id: int):
        """Soft or Hard-deletes a specific submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: for soft-delete if submission has feedback, or the deadline has passed,
            or it has already been (soft-)deleted, or it belongs to another student,
            or it was not found in the given lecture and assignment.
            for hard-delete if user is not an admin,
            or it was not found in the given lecture and assignment.
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        self.validate_parameters("hard_delete")
        hard_delete = self.get_argument("hard_delete", "false") == "true"

        try:
            submission = self.get_submission(lecture_id, assignment_id, submission_id)
            if submission is None:
                raise HTTPError(HTTPStatus.NOT_FOUND, reason="Submission was not found")

            if hard_delete:
                if not self.user.is_admin:
                    raise HTTPError(
                        HTTPStatus.FORBIDDEN, reason="Only Admins can hard-delete submission."
                    )

                self.session.delete(submission)
                self.session.commit()
                self.delete_submission_files(submission)
            else:
                # Do not allow students to delete other users' submissions
                if (
                    not self.user.is_admin
                    and self.get_role(lecture_id).role < Scope.instructor
                    and submission.user_id != self.user.id
                ):
                    raise HTTPError(HTTPStatus.NOT_FOUND, reason="Submission to delete not found.")

                if submission.feedback_status != FeedbackStatus.NOT_GENERATED:
                    raise HTTPError(
                        HTTPStatus.FORBIDDEN,
                        reason="Only submissions without feedback can be deleted.",
                    )

                # if assignment has deadline and it has already passed
                if (
                    submission.assignment.settings.deadline
                    and submission.assignment.settings.deadline
                    < datetime.datetime.now(datetime.timezone.utc)
                ):
                    raise HTTPError(
                        HTTPStatus.FORBIDDEN,
                        reason="Submission can't be deleted, due date of assigment has passed.",
                    )

                submission.deleted = DeleteState.deleted
                self.session.commit()
        except ObjectDeletedError:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Submission was not found")
        self.write("OK")


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
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Logs of submission were not found")


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
        except Exception as e:
            self.log.info(e)
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot parse properties file!")

        score = gradebook.score
        submission.grading_score = score
        submission.score = submission.score_scaling * score

        properties = SubmissionProperties(properties=properties_string, sub_id=submission.id)

        self.session.merge(properties)

        if submission.feedback_status == FeedbackStatus.GENERATED:
            submission.feedback_status = FeedbackStatus.FEEDBACK_OUTDATED

        if submission.manual_status == ManualStatus.MANUALLY_GRADED:
            submission.manually_graded = ManualStatus.BEING_EDITED

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
        """Creates or overwrites (resets) the repository which stores changes of
        submissions files
        :param lecture_id: lecture id
        :param assignment_id: assignment id
        :param submission_id: submission id
        :return:
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        self.validate_parameters()

        submission = self.get_submission(lecture_id, assignment_id, submission_id)
        if submission.commit_hash == INSTRUCTOR_SUBMISSION_COMMIT_CASH:
            raise HTTPError(
                HTTPStatus.BAD_REQUEST,
                reason="This repo cannot be edited or reset, because it was created by instructor",
            )

        assignment = submission.assignment
        lecture = assignment.lecture

        # Path to the (bare!) repository which will store edited submission files
        git_repo_path = self.construct_git_dir(
            repo_type=GitRepoType.EDIT,
            lecture=lecture,
            assignment=assignment,
            submission=submission,
        )

        # Path to repository of student which contains the submitted files
        submission_repo_path = os.path.join(
            self.gitbase, lecture.code, str(assignment.id), "user", submission.user.name
        )
        if not os.path.exists(submission_repo_path):
            raise HTTPError(
                HTTPStatus.BAD_REQUEST, reason="The user submission repository does not exist"
            )

        if os.path.exists(git_repo_path):
            shutil.rmtree(git_repo_path)

        # Creating bare repository
        if not os.path.exists(git_repo_path):
            os.makedirs(git_repo_path, exist_ok=True)

        await self._run_command_async(
            ["git", "init", "--bare", "--initial-branch=main"], git_repo_path
        )

        # Create temporary paths to copy the submission files in the edit repository
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
        await self._run_command_async(["git", "init", "--initial-branch=main"], tmp_input_path)

        # Pull user repository
        await self._run_command_async(
            ["git", "pull", str(submission_repo_path), "main"], tmp_input_path
        )
        self.log.info("Successfully cloned repo")

        # Checkout to correct submission commit
        await self._run_command_async(["git", "checkout", submission.commit_hash], tmp_input_path)
        self.log.info(f"Now at commit {submission.commit_hash}")

        # Copy files to output directory
        shutil.copytree(tmp_input_path, tmp_output_path, ignore=shutil.ignore_patterns(".git"))

        # Init local repository
        await self._run_command_async(["git", "init", "--initial-branch=main"], tmp_output_path)

        # Add edit remote
        await self._run_command_async(
            ["git", "remote", "add", "edit", str(git_repo_path)], tmp_output_path
        )
        self.log.info("Successfully added edit remote")

        # Switch to main
        await self._run_command_async(["git", "switch", "-c", "main"], tmp_output_path)
        self.log.info("Successfully switched to branch main")

        # Add files to staging
        await self._run_command_async(["git", "add", "-A"], tmp_output_path)
        self.log.info("Successfully added files to staging")

        # Commit Files
        await self._run_command_async(["git", "commit", "-m", "Initial commit"], tmp_output_path)
        self.log.info("Successfully commited files")

        # Push copied files
        await self._run_command_async(["git", "push", "edit", "main"], tmp_output_path)
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
                        Submission.auto_status == AutoStatus.AUTOMATICALLY_GRADED,
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
        submissions_model = [sub.serialize_with_user() for sub in submissions]

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
                raise HTTPError(500, reason="An unexpected error occurred.")
        else:
            raise HTTPError(403, reason="LTI plugin is not enabled by administrator.")


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
            .filter(Submission.assignid == assignment_id, Submission.user_id == role.user_id)
            .count()
        )

        self.write_json({"submission_count": usersubmissions_count})
        self.session.close()
