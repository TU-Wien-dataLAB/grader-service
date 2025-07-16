import os

from grader_service.auth.auth import Authenticator
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers.base_handler import BaseHandler
from grader_service.orm import User, Lecture
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope, Role
from traitlets import log as traitlets_log


logger = traitlets_log.get_logger()

logger.info("### loading service config")

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

from grader_service.auth.token import JupyterHubTokenAuthenticator

c.GraderService.authenticator_class = JupyterHubTokenAuthenticator

c.JupyterHubTokenAuthenticator.user_info_url = "http://localhost:8080/hub/api/user"


def post_auth_hook(authenticator: Authenticator, handler: BaseHandler, authentication: dict):
    log = handler.log
    log.info("post_auth_hook started")

    session = handler.session
    groups: list[str] = authentication["groups"]

    username = authentication["name"]
    user_model: User = session.query(User).get(username)
    if user_model is None:
        user_model = User()
        user_model.name = username
        user_model.display_name = username
        session.add(user_model)
        session.commit()

    for group in groups:
        if ":" in group:
            split_group = group.split(":")
            lecture_code = split_group[0]
            scope = split_group[1]
            scope = Scope[scope]

            lecture = session.query(Lecture).filter(Lecture.code == lecture_code).one_or_none()
            if lecture is None:
                lecture = Lecture()
                lecture.code = lecture_code
                lecture.name = lecture_code
                lecture.state = LectureState.active
                lecture.deleted = DeleteState.active
                session.add(lecture)
                session.commit()

            role = (
                session.query(Role)
                .filter(Role.username == username, Role.lectid == lecture.id)
                .one_or_none()
            )
            if role is None:
                log.info(f"No role for user {username} in lecture {lecture_code}... creating role")
                role = Role(username=username, lectid=lecture.id, role=scope)
                session.add(role)
                session.commit()
            else:
                log.info(
                    f"Found role {role.role.name} for user {username}  in lecture {lecture_code}... updating role to {scope.name}"
                )
                role.role = scope
                session.commit()
        else:
            log.info("Found group that doesn't match schema. Ignoring " + group)

    return authentication


c.Authenticator.post_auth_hook = post_auth_hook

c.Authenticator.allowed_users = {"admin", "instructor", "student", "tutor"}

c.Authenticator.admin_users = {"admin"}

c.GraderService.load_roles = {
    "lect1:instructor": ["admin", "instructor"],
    "lect1:student": ["student"],
    "lect1:tutor": ["tutor"],
}
