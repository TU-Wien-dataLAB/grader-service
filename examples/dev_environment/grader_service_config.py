import os

from grader_service.auth.auth import Authenticator
from grader_service.autograding.kube.kube_grader import KubeAutogradeExecutor
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers.base_handler import BaseHandler
from grader_service.orm import User, Lecture
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from grader_service.orm.takepart import Scope, Role

# from grader_service.autograding.docker_grader import DockerAutogradeExecutor

print("### loading service config")

c.GraderService.service_host = "127.0.0.1"
# existing directory to use as the base directory for the grader service
service_dir = os.path.expanduser("~/grader_service_dir")
c.GraderService.grader_service_dir = service_dir

c.JupyterHubGroupAuthenticator.hub_api_url = "http://127.0.0.1:8081/hub/api"

assert issubclass(KubeAutogradeExecutor, LocalAutogradeExecutor)
# c.RequestHandlerConfig.autograde_executor_class = DockerAutogradeExecutor
c.RequestHandlerConfig.autograde_executor_class = LocalAutogradeExecutor
c.LocalAutogradeExecutor.timeout_func = lambda l: 20

c.KubeAutogradeExecutor.kube_context = "minikube"
c.KubeAutogradeExecutor.resolve_image_name = lambda l, a: "ghcr.io/tu-wien-datalab/grader-labextension:main"

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


def get_role_from_auth(auth_state):
    user_role = 'student'
    for role in auth_state['https://purl.imsglobal.org/spec/lti/claim/roles']:
        if role.find('Instructor') >= 1:
            user_role = 'instructor'
            break
    return user_role


def post_auth_hook(authenticator: Authenticator, handler: BaseHandler, authentication: dict):
    print("####### POST AUTH HOOK")
    session = handler.session
    log = handler.log
    auth_state = authentication["auth_state"]

    username = authentication["name"]
    user_model: User = session.query(User).get(username)
    if user_model is None:
        user_model = User()
        user_model.name = username
        session.add(user_model)
        session.commit()

    lecture_code = auth_state["https://purl.imsglobal.org/spec/lti/claim/context"]["label"].replace(" ", "")
    lecture = session.query(Lecture).filter(Lecture.code == lecture_code).one_or_none()
    if lecture is None:
        lecture = Lecture()
        lecture.code = lecture_code
        lecture.name = lecture_code
        lecture.state = LectureState.active
        lecture.deleted = DeleteState.active
        session.add(lecture)
        session.commit()

    lti_role = get_role_from_auth(auth_state)
    scope = Scope[lti_role.lower()]
    log.info(f'Determined role {scope.name} for user {username}')

    role = session.query(Role).filter(Role.username == username, Role.lectid == lecture.id).one_or_none()
    if role is None:
        log.info(f'No role for user {username} in lecture {lecture_code}... creating role')
        role = Role(username=username, lectid=lecture.id, role=scope)
        session.add(role)
        session.commit()
    else:
        log.info(f'Found role {role.role.name} for user {username}  in lecture {lecture_code}... updating role to {scope.name}')
        role.role = scope
        session.commit()

    return authentication


c.Authenticator.post_auth_hook = post_auth_hook

## authenticator

# JupyterHub client config
c.GraderService.oauth_clients = [{
    'client_id': 'hub',
    'client_secret': 'hub',
    'redirect_uri': 'http://localhost:8080/hub/oauth_callback'
}]

from grader_service.auth.dummy import DummyAuthenticator
from grader_service.auth.pam import PAMAuthenticator
from grader_service.auth.oauth2 import OAuthenticator
from grader_service.auth.lti13.auth import LTI13Authenticator

c.GraderService.authenticator_class = DummyAuthenticator
#
# c.Authenticator.allowed_users = {'instructor', 'tutor', 'student1', 'student2' }
c.Authenticator.allow_all = True

c.DummyAuthenticator.password = 'test'
# c.Authenticator.admin_users = {'user1', 'user2', 'user3', 'user4'}
#
c.GraderService.load_roles = {"lect1:instructor": ["admin", "instructor", "user1"]}

# Moodle/LTI auth

# c.LTI13Authenticator.issuer = "http://localhost:8000"
# c.LTI13Authenticator.authorize_url = "http://localhost:8000/mod/lti/auth.php"
# # The platform's JWKS endpoint url providing public key sets used to verify the ID token
# c.LTI13Authenticator.jwks_endpoint = "http://localhost:8000/mod/lti/certs.php"
# # The external tool's client id as represented within the platform (LMS)
# c.LTI13Authenticator.client_id = ["ItOB9qSSRwH2yDa"]
# # calculate username using function defined in username.py
# c.LTI13Authenticator.uri_scheme = 'http'
