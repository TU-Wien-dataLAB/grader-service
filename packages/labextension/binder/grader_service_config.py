from grader_service.auth.dummy import DummyAuthenticator
from grader_service.autograding.local_grader import LocalAutogradeExecutor

print("Loading config file")

c.GraderService.service_host = "127.0.0.1"

import os

cwd = os.getcwd()
c.GraderService.grader_service_dir = os.path.join(cwd, "grader_service_dir")
c.GraderService.autograde_executor_class = LocalAutogradeExecutor

c.CeleryApp.conf = dict(
    broker_url="amqp://localhost",
    result_backend="rpc://",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
    task_always_eager=True,
)
c.CeleryApp.worker_kwargs = dict(concurrency=1, pool="prefork")

c.GraderService.authenticator_class = DummyAuthenticator
c.Authenticator.allowed_users = {"admin", "instructor", "student", "tutor"}
c.Authenticator.admin_users = {"admin"}
