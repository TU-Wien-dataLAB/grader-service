import asyncio
from typing import Union

from celery import Task
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker
from tornado.web import HTTPError

from grader_service.autograding.celery.app import CeleryApp
from grader_service.autograding.local_feedback import GenerateFeedbackExecutor
from grader_service.handlers.base_handler import RequestHandlerConfig
from grader_service.main import GraderService
from grader_service.orm import Submission, Assignment, Lecture
from grader_service.orm.base import DeleteState
from grader_service.plugins.lti import LTISyncGrades

# Note: CeleryApp.instance(config_path=...) has to be called before importing tasks.py otherwise the next line fails
celery = CeleryApp.instance()
Session = sessionmaker(bind=celery.db.engine)


class GraderTask(Task):
    def __init__(self) -> None:
        self._sessions = {}

    def before_start(self, task_id, args, kwargs):
        self._sessions[task_id] = Session()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session = self._sessions.pop(task_id)
        session.close()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self):
        return self._sessions[self.request.id]


@celery.app.task(bind=True, base=GraderTask)
def add(self: GraderTask, x, y):
    print(type(self.session))
    print("Adding {} and {}".format(x, y))
    return x + y


@celery.app.task(bind=True, base=GraderTask)
def autograde_task(self: GraderTask, lecture_id: int, assignment_id: int, sub_id: int):
    service = GraderService.instance()

    submission = self.session.query(Submission).get(sub_id)
    if submission is None or submission.assignment.id != assignment_id or submission.assignment.lecture.id != lecture_id:
        raise ValueError("incorrect submission")

    executor = RequestHandlerConfig.instance().autograde_executor_class(
        service.application.grader_service_dir, submission,
        config=service.application.config
    )
    asyncio.run(executor.start())
    celery.log.info(f"Autograding task of submission {submission.id} exited!")


@celery.app.task(bind=True, base=GraderTask)
def generate_feedback_task(self: GraderTask, lecture_id: int, assignment_id: int, sub_id: int):
    service = GraderService.instance()

    submission = self.session.query(Submission).get(sub_id)
    if submission is None or submission.assignment.id != assignment_id or submission.assignment.lecture.id != lecture_id:
        raise ValueError("incorrect submission")

    executor = GenerateFeedbackExecutor(
        service.application.grader_service_dir, submission,
        config=service.application.config
    )
    asyncio.run(executor.start())
    celery.log.info(f"Successfully generated feedback for submission {submission.id}!")


@celery.app.task(bind=True, base=GraderTask)
def lti_sync_task(self: GraderTask, lecture_id: int, assignment_id: int, sub_id: Union[int, None],
                  sync_on_feedback: bool) -> Union[dict, None]:
    assignment: Assignment = self.session.query(Assignment).get(assignment_id)
    if ((assignment is None) or (assignment.deleted == DeleteState.deleted)
            or (int(assignment.lectid) != int(lecture_id))):
        celery.log.error("Assignment with id " + str(assignment_id) + " was not found")
    lecture: Lecture = assignment.lecture

    if sub_id is None:
        # build the subquery
        subquery = (self.session.query(Submission.username, func.max(Submission.date).label("max_date"))
                    .filter(Submission.assignid == assignment_id, Submission.feedback_status)
                    .group_by(Submission.username)
                    .subquery())

        # build the main query
        submissions: list[Submission] = (
            self.session.query(Submission)
            .join(subquery,
                  (Submission.username == subquery.c.username) & (Submission.date == subquery.c.max_date) & (
                          Submission.assignid == assignment_id) & Submission.feedback_status)
            .all())

        data = (lecture.serialize(), assignment.serialize(), [s.serialize() for s in submissions])
    else:
        submission: Submission = self.session.query(Submission).get(sub_id)
        if submission is None or submission.assignment.id != assignment_id or submission.assignment.lecture.id != lecture_id:
            raise ValueError("incorrect submission")
        data = (lecture.serialize(), assignment.serialize(), [submission.serialize()])

    lti_plugin = LTISyncGrades.instance()
    if lti_plugin.check_if_lti_enabled(*data, sync_on_feedback=sync_on_feedback):
        try:
            results = asyncio.run(lti_plugin.start(*data))
            return results
        except HTTPError as e:
            celery.log.info("Could not sync grades: " + e.reason)
        except Exception as e:
            celery.log.error("Could not sync grades: " + str(e))
    else:
        celery.log.info("Skipping LTI plugin as it is not enabled")

    return None
