# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import shlex
import shutil
import time
from _decimal import Decimal

import jwt
import os.path
import subprocess
from http import HTTPStatus

from grader_service.autograding.grader_executor import GraderExecutor

from grader_service.autograding.local_feedback import GenerateFeedbackExecutor
from grader_service.handlers.handler_utils import parse_ids
import tornado
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.escape import url_escape, json_decode
from grader_service.api.models.submission import Submission as SubmissionModel
from grader_service.orm.assignment import AutoGradingBehaviour
from grader_service.orm.submission import Submission
from grader_service.orm.submission_logs import SubmissionLogs
from grader_service.orm.submission_properties import SubmissionProperties
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler
from sqlalchemy.sql.expression import func, distinct, text
from tornado.web import HTTPError
from grader_convert.gradebook.models import GradeBookModel
from subprocess import PIPE, CalledProcessError
from tornado.process import Subprocess

from grader_service.handlers.base_handler import GraderBaseHandler, authorize, RequestHandlerConfig
import datetime


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions.
    """

    def on_finish(self):
        # we do not close the session we just commit because we might run
        # LocalAutogradeExecutor or GenerateFeedbackExecutor in POST which still need it
        pass

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        """
        Return the submissions of an assignment.

        Two query parameter: latest, instructor-version.

        latest: only get the latest submissions of users.
        instructor-version: if true, get the submissions of all users in lecture if false, get own submissions.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if user is not authorized or the assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters("filter", "instructor-version", "format")
        submission_filter = self.get_argument("filter", "none")
        if submission_filter not in ["none", "latest", "best"]:
            raise HTTPError(HTTPStatus.BAD_REQUEST,
                            reason="Filter parameter has to be either 'none', 'latest' or 'best'")
        instructor_version = self.get_argument("instructor-version", None) == "true"
        response_format = self.get_argument("format", "json")
        if response_format not in ["json", "csv"]:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Response format can either be 'json' or 'csv'")

        role: Role = self.get_role(lecture_id)
        if instructor_version and role.role < Scope.tutor:
            raise HTTPError(HTTPStatus.FORBIDDEN, reason="Forbidden")
        assignment = self.get_assignment(lecture_id, assignment_id)

        if instructor_version:
            if submission_filter == 'latest':

                # build the subquery
                subquery = (self.session.query(Submission.username, func.max(Submission.date).label("max_date"))
                            .group_by(Submission.username)
                            .subquery())

                # build the main query
                submissions = (
                    self.session.query(Submission)
                    .join(subquery,
                          (Submission.username == subquery.c.username) & (Submission.date == subquery.c.max_date))
                    .all())

            elif submission_filter == 'best':

                # build the subquery
                subquery = (self.session.query(Submission.username, func.max(Submission.score).label("max_score"))
                            .group_by(Submission.username)
                            .subquery())

                # build the main query
                submissions = (
                    self.session.query(Submission)
                    .join(subquery,
                          (Submission.username == subquery.c.username) & (Submission.score == subquery.c.max_score))
                    .all())

            else:
                submissions = assignment.submissions
        else:
            if submission_filter == 'latest':
                # build the subquery
                subquery = (self.session.query(Submission.username, func.max(Submission.date).label("max_date"))
                            .group_by(Submission.username)
                            .subquery())

                # build the main query
                submissions = (
                    self.session.query(Submission)
                    .join(subquery,
                          (Submission.username == subquery.c.username) & (Submission.date == subquery.c.max_date))
                    .filter(
                        Submission.assignid == assignment_id,
                        Submission.username == role.username,)
                    .all())

            elif submission_filter == 'best':

                # build the subquery
                subquery = (self.session.query(Submission.username, func.max(Submission.score).label("max_score"))
                            .group_by(Submission.username)
                            .subquery())

                # build the main query
                submissions = (
                    self.session.query(Submission)
                    .join(subquery,
                          (Submission.username == subquery.c.username) & (Submission.score == subquery.c.max_score))
                    .filter(
                        Submission.assignid == assignment_id,
                        Submission.username == role.username, )
                    .all())
            else:
                submissions = (
                    self.session.query(
                        Submission
                    )
                    .filter(
                        Submission.assignid == assignment_id,
                        Submission.username == role.username,
                    )
                    .all()
                )
        if response_format == "csv":
            # csv format does not include logs
            self.set_header("Content-Type", "text/csv")
            for i, s in enumerate(submissions):
                d = s.model.to_dict()
                if i == 0:
                    self.write(",".join((k for k in d.keys() if k != "logs")) + "\n")
                self.write(",".join((str(v) for k, v in d.items() if k != "logs")) + "\n")
        else:
            self.write_json(submissions)
        self.session.close()  # manually close here because on_finish overwrite

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def post(self, lecture_id: int, assignment_id: int):
        """
        Create submission based on commit hash.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :raises HTTPError: throws err if user is not authorized or the assignment was not found
        """
        lecture_id, assignment_id = parse_ids(lecture_id, assignment_id)
        self.validate_parameters()
        body = tornado.escape.json_decode(self.request.body)
        try:
            commit_hash = body["commit_hash"]
        except KeyError:
            raise HTTPError(400, reason="Commit hash not found in body")

        role = self.get_role(lecture_id)
        assignment = self.get_assignment(lecture_id, assignment_id)
        if assignment.status == "complete":
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot submit completed assignment!")
        if role.role == Scope.student and assignment.status != "released":
            raise HTTPError(HTTPStatus.NOT_FOUND)
        submission_ts = datetime.datetime.utcnow()
        if assignment.duedate is not None and submission_ts > assignment.duedate:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Submission after due date of assignment!")
        if assignment.max_submissions and len(assignment.submissions) >= assignment.max_submissions:
            raise HTTPError(HTTPStatus.CONFLICT, reason="Maximum number of submissions reached!")

        submission = Submission()
        submission.assignid = assignment.id
        submission.date = submission_ts
        submission.username = self.user.name
        submission.feedback_available = False

        if assignment.duedate is not None and submission.date > assignment.duedate:
            self.write({"message": "Cannot submit assignment: Past due date!"})
            self.write_error(HTTPStatus.FORBIDDEN)

        git_repo_path = self.construct_git_dir(repo_type=assignment.type, lecture=assignment.lecture,
                                               assignment=assignment)
        if git_repo_path is None or not os.path.exists(git_repo_path):
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Git repository not found")

        try:
            subprocess.run(["git", "branch", "main", "--contains", commit_hash], cwd=git_repo_path, capture_output=True)
        except subprocess.CalledProcessError:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Commit not found")

        submission.commit_hash = commit_hash
        submission.auto_status = "not_graded"
        submission.manual_status = "not_graded"

        self.session.add(submission)
        self.session.commit()
        self.set_status(HTTPStatus.CREATED)
        self.write_json(submission)

        # If the assignment has automatic grading or fully automatic grading perform necessary operations
        if assignment.automatic_grading in [AutoGradingBehaviour.auto, AutoGradingBehaviour.full_auto]:
            self.set_status(HTTPStatus.ACCEPTED)
            executor = RequestHandlerConfig.instance().autograde_executor_class(
                self.application.grader_service_dir, submission, close_session=False, config=self.application.config
            )
            if assignment.automatic_grading == AutoGradingBehaviour.full_auto:
                feedback_executor = GenerateFeedbackExecutor(
                    self.application.grader_service_dir, submission, config=self.application.config
                )
                GraderExecutor.instance().submit(
                    executor.start,
                    on_finish=lambda: GraderExecutor.instance().submit(feedback_executor.start)
                )
            else:
                GraderExecutor.instance().submit(
                    executor.start,
                    lambda: self.log.info(f"Autograding task of submission {submission.id} exited!")
                )
        if assignment.automatic_grading == AutoGradingBehaviour.unassisted:
            self.session.close()


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionObjectHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/{submission_id}.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Returns a specific submission.

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
        if self.get_role(lecture_id).role == Scope.student and submission.username != self.user.name:
            raise HTTPError(HTTPStatus.NOT_FOUND)
        self.write_json(submission)

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Updates a specific submission and returns the updated entity.

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
        # sub.username = self.user.name
        sub.auto_status = sub_model.auto_status
        sub.manual_status = sub_model.manual_status
        sub.feedback_available = sub_model.feedback_available or False
        self.session.commit()
        self.write_json(sub)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/("
         r"?P<submission_id>\d*)\/logs\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionLogsHandler(GraderBaseHandler):
    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Returns logs of a submission.

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
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/properties\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionPropertiesHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to /lectures/{lecture_id}/assignments/{assignment_id}/submissions/
    {submission_id}/properties.
    """

    @authorize([Scope.student, Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Returns the properties of a submission,

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param submission_id: id of the submission
        :type submission_id: int
        :raises HTTPError: throws err if the submission or their properties are not found
        """
        lecture_id, assignment_id, submission_id = parse_ids(
            lecture_id, assignment_id, submission_id
        )
        properties = self.session.query(SubmissionProperties).get(submission_id)
        if properties is not None and properties.properties is not None:
            # delete source cells from properties if user is student
            if self.get_role(lecture_id).role == Scope.student:
                model = GradeBookModel.from_dict(json.loads(properties))
                for notebook in model.notebooks.values():
                    notebook.source_cells_dict = {}
                self.write(json.dumps(model.to_dict()))
            else:
                self.write(properties.properties)
        else:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Properties of submission were not found")

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Updates the properties of a submission.

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

        except Exception as e:
            self.log.info(e)
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot parse properties file!")

        submission.score = score

        properties = SubmissionProperties(properties=properties_string, sub_id=submission.id)

        self.session.merge(properties)

        self.session.commit()
        self.write_json(submission)

    def get_extra_credit(self, gradebook):
        extra_credit = 0
        for notebook in gradebook.notebooks.values():
            for grades in notebook.grades:
                extra_credit += grades.extra_credit if grades.extra_credit is not None else 0
        self.log.info("Extra credit is " + str(extra_credit))
        return extra_credit


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/(?P<submission_id>\d*)\/edit\/?",
    version_specifier=VersionSpecifier.ALL,
)
class SubmissionEditHandler(GraderBaseHandler):

    @authorize([Scope.tutor, Scope.instructor])
    async def put(self, lecture_id: int, assignment_id: int, submission_id: int):
        """
        Create or overwrites the repository which stores changes of submissions files
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
            self.gitbase,
            lecture.code,
            str(assignment.id),
            "edit",
            str(submission_id),
        )

        # Path to repository of student which contains the submitted files
        submission_repo_path = os.path.join(
            self.gitbase,
            lecture.code,
            str(assignment.id),
            assignment.type,
            submission.username
        )

        if os.path.exists(git_repo_path):
            shutil.rmtree(git_repo_path)

        # Creating bare repository
        if not os.path.exists(git_repo_path):
            os.makedirs(git_repo_path, exist_ok=True)

        await self._run_command(f'git init --bare', git_repo_path)

        # Create temporary paths to copy the submission files in the edit repository
        tmp_path = os.path.join(
            self.application.grader_service_dir,
            "tmp",
            lecture.code,
            str(assignment.id),
            "edit",
            str(submission.id),
        )

        tmp_input_path = os.path.join(
            tmp_path,
            "input"
        )

        tmp_output_path = os.path.join(
            tmp_path,
            "output"
        )

        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path, ignore_errors=True)

        os.makedirs(tmp_input_path, exist_ok=True)

        # Init local repository
        command = f"git init"
        await self._run_command(command, tmp_input_path)

        # Pull user repository
        command = f'git pull "{submission_repo_path}" main'
        await self._run_command(command, tmp_input_path)
        self.log.info("Successfully cloned repo")

        # Checkout to correct submission commit
        command = f"git checkout {submission.commit_hash}"
        await self._run_command(command, tmp_input_path)
        self.log.info(f"Now at commit {submission.commit_hash}")

        # Copy files to output directory
        shutil.copytree(tmp_input_path, tmp_output_path, ignore=shutil.ignore_patterns(".git"))

        # Init local repository
        command = f"git init"
        await self._run_command(command, tmp_output_path)

        # Add edit remote
        command = f"git remote add edit {git_repo_path}"
        await self._run_command(command, tmp_output_path)
        self.log.info("Successfully added edit remote")

        # Switch to main
        command = f"git switch -c main"
        await self._run_command(command, tmp_output_path)
        self.log.info("Successfully switched to branch main")

        # Add files to staging
        command = f"git add -A"
        await self._run_command(command, tmp_output_path)
        self.log.info("Successfully added files to staging")

        # Commit Files
        command = f'git commit -m "Initial commit" '
        await self._run_command(command, tmp_output_path)
        self.log.info("Successfully commited files")

        # Push copied files
        command = f"git push edit main"
        await self._run_command(command, tmp_output_path)
        self.log.info("Successfully pushed copied files")

        submission.edited = True
        self.session.commit()
        self.write_json(submission)


@register_handler(
    path=r"\/lectures\/(?P<lecture_id>\d*)\/assignments\/(?P<assignment_id>\d*)\/submissions\/lti\/?",
    version_specifier=VersionSpecifier.ALL,
)
class LtiSyncHandler(GraderBaseHandler):
    cache_token = {"token": None, "ttl": datetime.datetime.now()}

    @authorize([Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int):
        submissions = (
            self.session.query(
                Submission.id,
                Submission.username,
                Submission.score,
                func.max(Submission.date)
            )
            .filter(Submission.assignid == assignment_id, Submission.auto_status == "automatically_graded",
                    Submission.feedback_available == True)
            .group_by(Submission.username)
            .all()
        )

        assignment = self.get_assignment(lecture_id, assignment_id)

        lti_username_convert = RequestHandlerConfig.instance().lti_username_convert

        if lti_username_convert is None:
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason="Unable to match users: lti_username_convert is not set in grader "
                                   "config")

        scores = [{"id": s[0], "username": lti_username_convert(s[1]), "score": s[2]} for s in submissions]
        stamp = datetime.datetime.now()
        if LtiSyncHandler.cache_token["token"] and LtiSyncHandler.cache_token["ttl"] > stamp - datetime.timedelta(
                minutes=50):
            token = LtiSyncHandler.cache_token["token"]
        else:
            token = await self.request_bearer_token()
            LtiSyncHandler.cache_token["token"] = token
            LtiSyncHandler.cache_token["ttl"] = datetime.datetime.now()

        scores = {"assignment": assignment, "scores": scores, "token": token}

        self.write_json(scores)

    async def request_bearer_token(self):
        # get config variables
        lti_client_id = RequestHandlerConfig.instance().lti_client_id
        if lti_client_id is None:
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason="Unable to request bearer token: lti_client_id is not set in grader config")
        lti_token_url = RequestHandlerConfig.instance().lti_token_url
        if lti_token_url is None:
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason="Unable to request bearer token: lti_token_url is not set in grader config")

        private_key = RequestHandlerConfig.instance().lti_token_private_key
        if private_key is None:
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason="Unable to request bearer token: lti_token_private_key is not set in grader config")
        if callable(private_key):
            private_key = private_key()

        payload = {"iss": "grader-service", "sub": lti_client_id, "aud": [lti_token_url],
                   "ist": str(int(time.time())), "exp": str(int(time.time()) + 60),
                   "jti": str(int(time.time())) + "123"}
        try:
            encoded = jwt.encode(payload, private_key, algorithm="RS256")
        except Exception as e:
            raise HTTPError(HTTPStatus.UNPROCESSABLE_ENTITY, f"Unable to encode payload: {str(e)}")
        self.log.info("encoded: " + encoded)
        scopes = [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ]
        scopes = url_escape(" ".join(scopes))
        data = f"grant_type=client_credentials&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion" \
               f"-type%3Ajwt-bearer&client_assertion={encoded}&scope={scopes} "
        self.log.info("data: " + data)

        httpclient = AsyncHTTPClient()
        try:
            response = await httpclient.fetch(HTTPRequest(url=lti_token_url, method="POST", body=data,
                                                          headers={
                                                              "Content-Type": "application/x-www-form-urlencoded"}))
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason="Unable to request token:" + e.response.reason)
        return json_decode(response.body)["access_token"]
