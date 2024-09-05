import os
from grader_service.autograding.kube.kube_grader import KubeAutogradeExecutor
from grader_service.autograding.local_grader import LocalAutogradeExecutor

# from grader_service.autograding.docker_grader import DockerAutogradeExecutor

print("### loading service config")

c.GraderService.service_host = "127.0.0.1"
# existing directory to use as the base directory for the grader service
service_dir = os.path.expanduser("~/grader_service_dir")
c.GraderService.grader_service_dir = service_dir

c.JupyterHubGroupAuthenticator.hub_api_url = "http://127.0.0.1:8081/hub/api"

# c.LocalAutogradeExecutor.relative_input_path = "convert_in"
# c.LocalAutogradeExecutor.relative_output_path = "convert_out"

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
# c.Authenticator.allowed_users = {'instructor', 'tutor', 'student1', 'student2', 'matti.matt456@gmail.com', 'matthiasmatt', '2'}
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