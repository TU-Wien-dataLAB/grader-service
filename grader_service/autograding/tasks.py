import os
from functools import wraps
from typing import Union, Any, ParamSpec, Callable

from celery import Celery, Task
from celery.result import AsyncResult
from celery.utils.log import get_task_logger
from traitlets import Dict
from traitlets.config import SingletonConfigurable

log = get_task_logger(__name__)


class CeleryApp(SingletonConfigurable):
    conf = Dict(default_value=dict(
        broker_url='pyamqp://',
        result_backend='rpc://',
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
    ), help="Configuration for Celery app.").tag(config=True)

    _app: Union[Celery, None] = None

    @property
    def app(self):
        if self._app is None:
            self._app = Celery(main="grader_service")
            self._app.conf.update(self.conf)
        return self._app


_P = ParamSpec("_P")


def grader_task(*args: Any, **kwargs: Any):
    app = CeleryApp.instance().app

    def _decorator(func: Callable[_P, AsyncResult]) -> Callable[_P, AsyncResult]:
        @app.task(*args, **kwargs)
        @wraps(func)
        def _decorated(*t_args: _P.args, **t_kwargs: _P.kwargs):
            return func(*t_args, **t_kwargs)

        return _decorated

    return _decorator


@grader_task(bind=True)
def one(self: Task):
    log.info(f"Running task {self.name}")
    return 1
