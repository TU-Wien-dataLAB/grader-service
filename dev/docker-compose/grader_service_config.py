import os
from typing import Optional

from jupyterhub.auth import Authenticator
from traitlets import log as traitlets_log

from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.auth.token import JupyterHubTokenAuthenticator

from grader_service.handlers.base_handler import BaseHandler
from grader_service.orm import User, Lecture
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope, Role


logger = traitlets_log.get_logger()

c.GraderService.service_host = "0.0.0.0"
c.GraderService.service_port = 4010
c.GraderService.grader_service_dir = "/app/service_dir"

# choose the right db_url based on the environment variable
database_type = os.getenv("DATABASE_TYPE")
db_url = ""
if database_type == "sqlite":
    db_url = "sqlite:///grader.db"
elif database_type == "postgres":
    db_url = "postgresql://postgres:postgres@postgres:5432/grader"
else:
    logger.error("Unknown database type")

c.GraderService.db_url = db_url

c.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor
c.LocalAutogradeExecutor.default_cell_timeout = 200

# get rabbitmq username and password
rabbit_mq_username = os.getenv("RABBITMQ_GRADER_SERVICE_USERNAME")
rabbit_mq_password = os.getenv("RABBITMQ_GRADER_SERVICE_PASSWORD")

c.CeleryApp.conf = dict(
    broker_url=f"amqp://{rabbit_mq_username}:{rabbit_mq_password}@rabbitmq:5672/grader",
    result_backend="rpc://",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    broker_connection_retry_on_startup=True,
)


c.GraderService.authenticator_class = JupyterHubTokenAuthenticator


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
            log.info("Found group that doesn't match schema. Ignoring " + group)

    return authentication


c.Authenticator.post_auth_hook = post_auth_hook

c.JupyterHubTokenAuthenticator.user_info_url = "http://hub:8080/hub/api/user"
c.Authenticator.admin_users = {"admin"}
c.Authenticator.allow_all = True
