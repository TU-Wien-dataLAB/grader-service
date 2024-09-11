from typing import Union
from tornado_sqlalchemy import SQLAlchemy
from traitlets import Dict
from traitlets.config import SingletonConfigurable, MultipleInstanceError
from celery import Celery, current_app


class CeleryApp(SingletonConfigurable):
    conf = Dict(default_value=dict(
        broker_url='amqp://localhost',
        result_backend='rpc://',
        task_serializer='json',
        result_serializer='json',
        accept_content=['json'],
        broker_connection_retry_on_startup=True
    ), help="Configuration for Celery app.").tag(config=True)

    worker_kwargs = Dict(default_value={}, help="Keyword arguments to pass to celery Worker instance.").tag(config=True)

    app: Celery
    _db: Union[SQLAlchemy, None] = None

    def __init__(self, config_file: Union[str, None] = None, **kwargs):
        super().__init__(**kwargs)
        if not self.config:
            self.config_file = config_file
            if config_file is None:
                raise ValueError("Neither config nor config_path were passed to CeleryApp!")

            from grader_service.main import GraderService
            service = GraderService.instance()
            # config might not be loaded if the celery app was not initialized by the service (e.g. in a worker)
            if len(service.loaded_config_files) == 0:
                self.log.info(f"Loading GraderService config from {config_file}")
                service.load_config_file(self.config_file)
                service.set_config()
                self.update_config(service.config)

        from grader_service.autograding.celery.tasks import app
        self.app = app  # update module level celery app from tasks.py
        self.app.conf.update(self.conf)

    @property
    def db(self) -> SQLAlchemy:
        if self._db is None:
            self.log.info('Instantiating database connection')
            from grader_service.main import GraderService, db
            db_url = GraderService.instance().db_url
            self.log.info(f"Database URL: {db_url}")
            self._db = db(db_url)
        return self._db
