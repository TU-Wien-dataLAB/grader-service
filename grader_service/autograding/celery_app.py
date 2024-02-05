from typing import Union
from tornado_sqlalchemy import SQLAlchemy
from traitlets import Dict
from traitlets.config import SingletonConfigurable, MultipleInstanceError
from celery import Celery


class CeleryApp(SingletonConfigurable):
    conf = Dict(default_value=dict(
        broker_url='pyamqp://',
        result_backend='rpc://',
        task_serializer='json',
        result_serializer='json',
        accept_content=['json']
    ), help="Configuration for Celery app.").tag(config=True)

    _app: Union[Celery, None] = None
    _db: Union[SQLAlchemy, None] = None

    def __init__(self, config_file: str, **kwargs):
        super().__init__(**kwargs)
        self.config_file = config_file
        try:
            from grader_service.main import GraderService
            service = GraderService.instance()
            # config might not be loaded if the celery app was not initialized by the service (e.g. in a worker)
            if not service.config:
                service.load_config_file(self.config_file)
                self.update_config(service.config)
        except MultipleInstanceError:
            # instance exists and probably has a different module (e.g. __main__) -> config exists
            pass

    @property
    def app(self):
        if self._app is None:
            self._app = Celery(main="grader_service", include=['grader_service'])
            self._app.conf.update(self.conf)
        return self._app

    @property
    def db(self) -> SQLAlchemy:
        if self._db is None:
            from grader_service.main import GraderService, db
            service = GraderService.instance()
            # service config is always loaded because it is either initialized when the service was started
            # or when this class was initialized so db_url must be set
            self._db = db(service.db_url)
        return self._db

