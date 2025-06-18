# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
from http import HTTPStatus

import celery

from grader_service.autograding.celery.tasks import (
    autograde_task,
    generate_feedback_task,
    lti_sync_task,
)
from grader_service.handlers.base_handler import GraderBaseHandler, authorize
from grader_service.orm.submission import Submission
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler

from .handler_utils import parse_ids


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments"
    + r"\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/auto\/?",
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
        lecture_id, assignment_id, sub_id = parse_ids(lecture_id, assignment_id, sub_id)
        self.validate_parameters()
        submission = self.get_submission(lecture_id, assignment_id, sub_id)
        submission.auto_status = "pending"
        if submission.feedback_status == "generated":
            submission.feedback_status = "feedback_outdated"
        self.session.commit()

        submission = self.session.get(Submission, sub_id)

        autograde_task.delay(lecture_id, assignment_id, sub_id)
        self.set_status(HTTPStatus.ACCEPTED, reason="Autograding submission process started")

        self.write_json(submission)


@register_handler(
    path=r"\/api\/lectures\/(?P<lecture_id>\d*)\/assignments"
    + r"\/(?P<assignment_id>\d*)\/grading\/(?P<sub_id>\d*)\/feedback\/?",
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

    @authorize([Scope.tutor, Scope.instructor])
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
        lecture_id, assignment_id, sub_id = parse_ids(lecture_id, assignment_id, sub_id)
        self.validate_parameters()
        lecture = self.get_lecture(lecture_id)
        assignment = self.get_assignment(lecture_id, assignment_id)
        submission: Submission = self.get_submission(lecture_id, assignment_id, sub_id)
        submission.feedback_status = "generating"
        self.session.commit()
        # use immutable signature: https://docs.celeryq.dev/en/stable/reference/celery.app.task.html#celery.app.task.Task.si
        generate_feedback_chain = celery.chain(
            generate_feedback_task.si(lecture_id, assignment_id, sub_id),
            lti_sync_task.si(
                lecture.serialize(),
                assignment.serialize(),
                [submission.serialize()],
                sync_on_feedback=True,
            ),
        )
        generate_feedback_chain()

        self.set_status(HTTPStatus.ACCEPTED, reason="Generating feedback process started")
        self.write_json(submission)
