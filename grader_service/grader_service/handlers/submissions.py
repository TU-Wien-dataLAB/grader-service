# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import json
import time

import jwt
import os.path
import subprocess
from http import HTTPStatus
import cachetools.func
from traitlets import Unicode, Callable, Union
from traitlets.config import LoggingConfigurable, SingletonConfigurable, Configurable
from functools import lru_cache

from grader_service.autograding.grader_executor import GraderExecutor

from grader_service.autograding.local_feedback import GenerateFeedbackExecutor
from grader_service.handlers.handler_utils import parse_ids
import tornado
from tornado.httpclient import AsyncHTTPClient, HTTPRequest, HTTPClientError
from tornado.escape import url_escape, json_decode
from grader_service.api.models.submission import Submission as SubmissionModel
from grader_service.orm.assignment import AutoGradingBehaviour
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Role, Scope
from grader_service.registry import VersionSpecifier, register_handler
from sqlalchemy.sql.expression import func
from tornado.web import HTTPError
from grader_convert.gradebook.models import GradeBookModel

from grader_service.handlers.base_handler import GraderBaseHandler, authorize, RequestHandlerConfig
import datetime


def tuple_to_submission(t, student=False):
    """
    Transforms tuple with values into a submission entity.

    :param student: if True, get submissions for student where some data is not needed
    :param t: tuple with values
    :return: submission entity
    """
    s = Submission()
    (
        s.id,
        s.auto_status,
        s.manual_status,
        s.score,
        s.username,
        s.assignid,
        s.commit_hash,
        s.feedback_available,
        s.logs,
        s.date,
    ) = t

    if student:
        s.logs = None
        s.commit_hash = None
        s.score = s.score if s.feedback_available else 0

    return s


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
                submissions = (
                    self.session.query(
                        Submission.id,
                        Submission.auto_status,
                        Submission.manual_status,
                        Submission.score,
                        Submission.username,
                        Submission.assignid,
                        Submission.commit_hash,
                        Submission.feedback_available,
                        Submission.logs,
                        func.max(Submission.date),
                    )
                    .filter(Submission.assignid == assignment_id)
                    .group_by(Submission.username)
                    .all()
                )
                submissions = [tuple_to_submission(t) for t in submissions]
            elif submission_filter == 'best':
                submissions = (
                    self.session.query(
                        Submission.id,
                        Submission.auto_status,
                        Submission.manual_status,
                        func.max(Submission.score),
                        Submission.username,
                        Submission.assignid,
                        Submission.commit_hash,
                        Submission.feedback_available,
                        Submission.logs,
                        Submission.date,
                    )
                    .filter(Submission.assignid == assignment_id)
                    .group_by(Submission.username)
                    .all()
                )
                submissions = [tuple_to_submission(t) for t in submissions]
            else:
                submissions = assignment.submissions
        else:
            if submission_filter == 'latest':
                submissions = (
                    self.session.query(
                        Submission.id,
                        Submission.auto_status,
                        Submission.manual_status,
                        Submission.score,
                        Submission.username,
                        Submission.assignid,
                        Submission.commit_hash,
                        Submission.feedback_available,
                        Submission.logs,
                        func.max(Submission.date),
                    )
                    .filter(
                        Submission.assignid == assignment_id,
                        Submission.username == role.username,
                    )
                    .group_by(Submission.username)
                    .all()
                )
                submissions = [tuple_to_submission(t, True) for t in submissions]
            elif submission_filter == 'best':
                submissions = (
                    self.session.query(
                        Submission.id,
                        Submission.auto_status,
                        Submission.manual_status,
                        func.max(Submission.score),
                        Submission.username,
                        Submission.assignid,
                        Submission.commit_hash,
                        Submission.feedback_available,
                        Submission.logs,
                        Submission.date,
                    )
                    .filter(
                        Submission.assignid == assignment_id,
                        Submission.username == role.username,
                    )
                    .group_by(Submission.username)
                    .all()
                )
                submissions = [tuple_to_submission(t, True) for t in submissions]
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
        submission = self.get_submission(lecture_id, assignment_id, submission_id)
        if submission.properties is not None:
            # delete source cells from properties if user is student
            if self.get_role(lecture_id).role == Scope.student:
                model = GradeBookModel.from_dict(json.loads(submission.properties))
                for notebook in model.notebooks.values():
                    notebook.source_cells_dict = {}
                self.write(json.dumps(model.to_dict()))
            else:
                self.write(submission.properties)
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

            score = gradebook.score + self.get_extra_credit(gradebook)

        except:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Cannot parse properties file!")
        submission.score = score
        submission.properties = properties_string
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
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Unable to match users: lti_username_convert is not set in grader "
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
        encoded = jwt.encode(payload, private_key, algorithm="RS256")
        scopes = [
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"
        ]
        scopes = url_escape(" ".join(scopes))
        data = f"grant_type=client_credentials&client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion" \
               f"-type%3Ajwt-bearer&client_assertion={encoded}&scope={scopes} "

        httpclient = AsyncHTTPClient()
        try:
            response = await httpclient.fetch(HTTPRequest(url=lti_token_url, method="POST", body=data,
                                                          headers={
                                                              "Content-Type": "application/x-www-form-urlencoded"}))
        except HTTPClientError as e:
            self.log.error(e.response)
            raise HTTPError(e.code, reason=e.response.reason)
        return json_decode(response.body)["access_token"]
