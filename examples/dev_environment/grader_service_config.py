import os

from grader_service.auth.auth import Authenticator
from grader_service.autograding.kube.kube_grader import KubeAutogradeExecutor
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers.base_handler import BaseHandler
from grader_service.orm import User, Lecture
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope, Role

# TODO: Only use DummyAuthenticator

# from grader_service.autograding.docker_grader import DockerAutogradeExecutor

print("### loading service config")

c.GraderService.service_host = "127.0.0.1"
# existing directory to use as the base directory for the grader service
service_dir = os.path.join(os.getcwd(), "service_dir")
c.GraderService.grader_service_dir = service_dir

c.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor

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


# JupyterHub client config
c.GraderService.oauth_clients = [
    {
        "client_id": "my_id",
        "client_secret": "my_secret",
        "redirect_uri": "http://localhost:8080/hub/oauth_callback",
    }
]

from grader_service.auth.dummy import DummyAuthenticator

c.GraderService.authenticator_class = DummyAuthenticator
c.Authenticator.allowed_users = {"admin", "instructor", "student", "tutor"}
c.Authenticator.admin_users = {"admin"}
c.GraderService.load_roles = {
    "lect1": {"members": ["admin", "instructor"], "role": "instructor"},
    "lect1": {"members": ["tutor"], "role": "tutor"},
    "lect1": {"members": ["student"], "role": "student"},
}
