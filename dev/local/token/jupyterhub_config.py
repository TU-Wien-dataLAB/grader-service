import os
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.escape import json_encode, json_decode

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
c.JupyterHub.spawner_class = "jupyterhub.spawner.SimpleLocalProcessSpawner"
c.SimpleLocalProcessSpawner.home_dir_template = os.path.join(os.getcwd(), "home_dir", "{username}")


async def pre_spawn_hook(spawner):
    http_client = AsyncHTTPClient()
    data = {"token": spawner.api_token}
    request = HTTPRequest(
        url="http://localhost:4010/services/grader/login", method="POST", body=json_encode(data)
    )

    response = await http_client.fetch(request=request)
    grader_api_token = json_decode(response.body)["api_token"]
    spawner.environment.update({"GRADER_API_TOKEN": grader_api_token})


c.Spawner.pre_spawn_hook = pre_spawn_hook

## simple setup
c.JupyterHub.ip = "127.0.0.1"
c.JupyterHub.port = 8080

c.JupyterHub.services.append(
    {
        "name": "grader",
        "url": "http://127.0.0.1:4010",
        "api_token": "7572f93a2e7640999427d9289c8318c0",
    }
)

c.JupyterHub.log_level = "INFO"
