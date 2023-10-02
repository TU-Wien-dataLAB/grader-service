# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus
from tornado.web import HTTPError

from grader_service.autograding.local_feedback import GenerateFeedbackExecutor
from grader_service.autograding.grader_executor import GraderExecutor
from grader_service.orm.assignment import Assignment
from grader_service.orm.lecture import Lecture
from grader_service.plugins.lti import LTISyncGrades
from .handler_utils import parse_ids
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler

from grader_service.handlers.base_handler import GraderBaseHandler, authorize,\
    RequestHandlerConfig


@register_handler(
    path=r'\/lectures\/(?P<lecture_id>\d*)\/assignments' +
    r'\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/auto\/?',
    version_specifier=VersionSpecifier.ALL,
)
class GradingAutoHandler(GraderBaseHandler):
    """Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/grading
    /{submission_id}/auto.
    """
    def on_finish(self):
        # we do not close the session we just commit
        # because LocalAutogradeExecutor still needs it
        if self.session:
            self.session.commit()

    @authorize([Scope.tutor, Scope.instructor])
    async def get(self, lecture_id: int, assignment_id: int, sub_id: int):
        """
        Starts the autograding process of a submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        :raises HTTPError: throws err if the submission was not found
        """
        lecture_id, assignment_id, sub_id = parse_ids(
            lecture_id, assignment_id, sub_id)
        self.validate_parameters()
        submission = self.get_submission(lecture_id, assignment_id, sub_id)
        executor = RequestHandlerConfig.instance().autograde_executor_class(
            self.application.grader_service_dir, submission,
            config=self.application.config
        )
        GraderExecutor.instance().submit(
            executor.start,
            lambda: self.log.info(f"Autograding task of submission \
                {submission.id} exited!")
        )
        submission = self.session.query(Submission).get(sub_id)
        self.set_status(HTTPStatus.ACCEPTED,
                        reason="Autograding submission process started")
        
        self.write_json(submission)


@register_handler(
    path=r'\/lectures\/(?P<lecture_id>\d*)\/assignments' +
    r'\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/feedback\/?',
    version_specifier=VersionSpecifier.ALL,
)
class GenerateFeedbackHandler(GraderBaseHandler):
    """
    Tornado Handler class for http requests to
    /lectures/{lecture_id}/assignments/{assignment_id}/grading/
    {submission_id}/feedback.
    """
    def on_finish(self):
        # we do not close the session we just commit
        # because GenerateFeedbackHandler still needs it
        if self.session:
            self.session.commit()

    async def get(self, lecture_id: int, assignment_id: int, sub_id):
        """
        Starts the process of generating feedback for a submission.

        :param lecture_id: id of the lecture
        :type lecture_id: int
        :param assignment_id: id of the assignment
        :type assignment_id: int
        :param sub_id: id of the submission
        :type sub_id: int
        :raises HTTPError: throws err if the submission was not found
        """
        lecture_id, assignment_id, sub_id = parse_ids(
            lecture_id, assignment_id, sub_id)
        self.validate_parameters()
        submission : Submission = self.get_submission(lecture_id, assignment_id, sub_id)
        executor = GenerateFeedbackExecutor(
            self.application.grader_service_dir, submission,
            config=self.application.config
        )
        GraderExecutor.instance().submit(
            executor.start,
            lambda: self.log.info(f"Successfully generated feedback \
             for submission {submission.id}!")
        )
        self.set_status(HTTPStatus.ACCEPTED,
                        reason="Generating feedback process started")
        
        lecture: Lecture = self.session.get(Lecture, lecture_id)
        assignment: Assignment = self.session.get(Assignment, assignment_id)

        lti_plugin = LTISyncGrades.instance()
        data = (lecture.serialize(), assignment.serialize(), [submission.serialize()])

        if lti_plugin.check_if_lti_enabled(*data, sync_on_feedback=True):

            try:
                await lti_plugin.start(*data)
            except HTTPError as e:
                self.write_error(e.status_code, reason=e.reason)
                self.log.info("Could not sync grades: " + e.reason )
            except Exception as e:
                self.log.error("Could not sync grades: " + str(e))

        self.write_json(submission)
