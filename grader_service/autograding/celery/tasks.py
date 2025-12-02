import asyncio
from typing import Union

from celery import Celery, Task
from tornado.web import HTTPError

from grader_service.autograding.celery.app import CeleryApp
from grader_service.autograding.local_feedback import LocalFeedbackExecutor
from grader_service.handlers.base_handler import RequestHandlerConfig
from grader_service.orm.submission import FeedbackStatus, Submission
from grader_service.plugins.lti import LTISyncGrades

# Note: The celery instance is lazy so we can still add configuration later
app = Celery(set_as_current=True)


class GraderTask(Task):
    def __init__(self) -> None:
        self.celery = CeleryApp.instance()
        self.log = self.celery.log
        self.Session = self.celery.sessionmaker
        self._sessions = {}

    def before_start(self, task_id, args, kwargs):
        self._sessions[task_id] = self.Session()
        super().before_start(task_id, args, kwargs)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        session = self._sessions.pop(task_id)
        session.close()
        super().after_return(status, retval, task_id, args, kwargs, einfo)

    @property
    def session(self):
        return self._sessions[self.request.id]


@app.task(bind=True, base=GraderTask)
def add(self: GraderTask, x, y):
    print(type(self.session))
    print("Adding {} and {}".format(x, y))
    return x + y


@app.task(bind=True, base=GraderTask)
def autograde_task(self: GraderTask, lecture_id: int, assignment_id: int, sub_id: int):
    from grader_service.main import GraderService

    grader_service_dir = GraderService.instance().grader_service_dir

    submission = self.session.get(Submission, sub_id)
    if submission is None:
        raise ValueError("Submission not found")
    if submission.assignment.id != assignment_id or submission.assignment.lecture.id != lecture_id:
        raise ValueError(
            f"invalid submission {submission.id}: {assignment_id=:}, {lecture_id=:} does not match"
        )

    executor = RequestHandlerConfig.instance().autograde_executor_class(
        grader_service_dir, submission, config=self.celery.config
    )
    self.log.info(f"Running autograding task for submission {submission.id}")
    executor.start()
    self.log.info(f"Autograding task of submission {submission.id} exited!")


@app.task(bind=True, base=GraderTask)
def generate_feedback_task(self: GraderTask, lecture_id: int, assignment_id: int, sub_id: int):
    from grader_service.main import GraderService

    grader_service_dir = GraderService(config=self.celery.config).grader_service_dir

    submission = self.session.get(Submission, sub_id)
    if submission is None:
        raise ValueError("Submission not found")
    if submission.assignment.id != assignment_id or submission.assignment.lecture.id != lecture_id:
        raise ValueError(
            f"invalid submission {submission.id}: {assignment_id=:}, {lecture_id=:} does not match"
        )

    executor = LocalFeedbackExecutor(grader_service_dir, submission, config=self.celery.config)
    executor.start()
    if submission.feedback_status == FeedbackStatus.GENERATED:
        self.log.info("Successfully generated feedback for submission %s!", submission.id)
    else:
        self.log.error("Failed to generate feedback for submission %s!", submission.id)


@app.task(bind=True, base=GraderTask)
def lti_sync_task(
    self: GraderTask,
    lecture: dict,
    assignment: dict,
    submissions: list[dict],
    feedback_sync: bool = False,
) -> Union[dict, None]:
    """Gathers submissions based on params and starts LTI sync process
    :param lecture: lecture object
    :param assignment: assignment object
    :param submissions: submissions to be synced (including user information)
    :param feedback_sync(optional): if True, the sync task was started by a feedback generation
    """
    lti_plugin = LTISyncGrades.instance()
    # check if the lti plugin is enabled
    if lti_plugin.check_if_lti_enabled(
        lecture, assignment, submissions, feedback_sync=feedback_sync
    ):
        try:
            results = asyncio.run(lti_plugin.start(lecture, assignment, submissions))
            return results
        except HTTPError as e:
            err_msg = f"Could not sync grades: {e.reason}"
            self.log.info(err_msg)
            raise e
        except Exception as e:
            self.log.error("Could not sync grades: " + str(e))
            raise HTTPError(500, reason="An unexpected error occured.")
    else:
        # if the synchronisation task is automatic only log event
        if feedback_sync:
            self.log.info("Skipping LTI grade synchronisation, because it is not enabled")
        else:
            # else tell the user that the plugin is disabled
            raise HTTPError(403, reason="LTI plugin is not enabled by administator.")
    return None
