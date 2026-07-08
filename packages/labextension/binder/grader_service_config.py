print("Loading config file")

import os

from grader_service.autograding.local_grader import LocalAutogradeExecutor

c.GraderService.service_host = "127.0.0.1"

import os
cwd = os.getcwd()
c.GraderService.grader_service_dir = os.path.join(cwd, "grader_service_dir")

c.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor

c.CeleryApp.conf = dict(
    broker_url='amqp://localhost',
    result_backend='rpc://',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    broker_connection_retry_on_startup=True,
    task_always_eager=True
)
c.CeleryApp.worker_kwargs = dict(concurrency=1, pool="prefork")

from grader_service.auth.dummy import DummyAuthenticator

c.GraderService.authenticator_class = DummyAuthenticator
c.Authenticator.allowed_users = {'admin', 'instructor', 'student', 'tutor'}
c.Authenticator.admin_users = {'admin'}
