import os

from tornado.escape import json_decode, json_encode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

## generic
c.JupyterHub.admin_access = True
c.Spawner.default_url = "/lab"
c.Spawner.cmd = ["jupyter-labhub"]

## authenticator
from jupyterhub.auth import DummyAuthenticator

c.JupyterHub.authenticator_class = DummyAuthenticator
c.Authenticator.allowed_users = {"admin", "instructor", "tutor", "student"}
c.Authenticator.admin_users = {"admin"}
c.JupyterHub.load_groups = {
    "lect1:instructor": {"users": ["admin", "instructor"]},
    "lect1:student": {"users": ["student"]},
    "lect1:tutor": {"users": ["tutor"]},
}

c.Authenticator.enable_auth_state = True

## spawner
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = "grader_network"

c.DockerSpawner.remove = True

# Todo: make sensible image choice like local version of labextension
c.DockerSpawner.image = "ghcr.io/tu-wien-datalab/grader-labextension:latest"
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}


async def pre_spawn_hook(spawner):
    http_client = AsyncHTTPClient()
    data = {"token": spawner.api_token}
    request = HTTPRequest(
        url="http://service:4010/services/grader/login", method="POST", body=json_encode(data)
    )

    response = await http_client.fetch(request=request)
    grader_api_token = json_decode(response.body)["api_token"]
    spawner.environment.update({"GRADER_API_TOKEN": grader_api_token})
    spawner.environment.update({"GRADER_HOST_URL": "http://service:4010"})
    spawner.environment.update({"JUPYTERHUB_API_URL": "http://hub:8080/hub/api"})


c.Spawner.pre_spawn_hook = pre_spawn_hook
## simple setup
c.JupyterHub.bind_url = "http://0.0.0.0:8080"

c.JupyterHub.proxy_check_ip = False


c.JupyterHub.services.append(
    {
        "name": "grader",
        "url": "http://service:4010",
        "api_token": "7572f93a2e7640999427d9289c8318c0",
    }
)

c.JupyterHub.log_level = "INFO"
