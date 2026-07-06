import os
from typing import Optional

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
    user_model: Optional[User] = session.query(User).filter(User.name == username).one_or_none()
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
                .filter(Role.user_id == user_model.id, Role.lectid == lecture.id)
                .one_or_none()
            )
            if role is None:
                log.info(
                    "No role for user %s in lecture %s... creating role", username, lecture_code
                )
                role = Role(user_id=user_model.id, lectid=lecture.id, role=scope)
                session.add(role)
                session.commit()
            else:
                log.info(
                    "Found role %s for user %s in lecture %s... updating role to %s",
                    role.role.name,
                    username,
                    lecture_code,
                    scope.name,
                )
                role.role = scope
                session.commit()
        else:
            log.info("Found group that doesn't match schema. Ignoring %s", group)

    return authentication


c.Authenticator.post_auth_hook = post_auth_hook

c.Authenticator.allowed_users = {"admin", "instructor", "student", "tutor"}

c.Authenticator.admin_users = {"admin"}

c.GraderService.load_roles = {
    "lecture1": [
        {"members": ["student"], "role": "student"},
        {"members": ["tutor"], "role": "tutor"},
        {"members": ["instructor", "admin"], "role": "instructor"},
    ]
}
