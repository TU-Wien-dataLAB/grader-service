from celery import Task
from sqlalchemy.orm import sessionmaker

from grader_service.autograding.celery_app import CeleryApp

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
