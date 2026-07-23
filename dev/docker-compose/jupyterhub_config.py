import os

from jupyterhub.auth import DummyAuthenticator
from tornado.escape import json_decode, json_encode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

## generic
c.JupyterHub.admin_access = True
c.Spawner.default_url = "/lab"
# The watcher entrypoint starts `jlpm watch` (tsc -w + jupyter labextension
# watch) in the background, then hands off to jupyter-labhub so labextension TS
# changes are hot-reloaded in spawned user pods.
c.Spawner.cmd = ["/usr/local/bin/entrypoint-labextension.sh", "jupyter-labhub"]

## authenticator
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
c.DockerSpawner.network_name = "grader-dev_grader-network"

c.DockerSpawner.remove = True

# Local dev image with the labextension installed in editable mode (built by the
# `labextension` compose service / `make dev-up`).
c.DockerSpawner.image = "grader-labextension:dev"
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

# Bind-mount labextension source inputs into the pod so the in-pod watcher
# rebuilds on save. GRADER_REPO_ROOT is the absolute host path to the repo root
# (set by `make dev-up`). Only the read-only source inputs (src/, schema/,
# style/) are mounted: the watcher writes lib/ and grader_labextension/
# labextension/ into the image's jovyan-owned tree (served via the symlink
# created in the image), which avoids host-UID mismatch on the build output.
_repo_root = os.environ.get("GRADER_REPO_ROOT", "")
_labext_src = os.path.join(_repo_root, "packages", "labextension") if _repo_root else ""
c.DockerSpawner.volumes = {"jupyterhub-data-{username}": notebook_dir}
if _labext_src:
    c.DockerSpawner.volumes.update(
        {
            f"{_labext_src}/src": "/opt/grader-labextension/src",
            f"{_labext_src}/schema": "/opt/grader-labextension/schema",
            f"{_labext_src}/style": "/opt/grader-labextension/style",
        }
    )
else:
    print(
        "WARNING: GRADER_REPO_ROOT is not set; labextension source is not "
        "bind-mounted into spawned pods (no hot reload). Run via `make dev-up`."
    )


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


# Use environment variable if set, otherwise let JupyterHub auto-generate one
if os.environ.get("GRADER_API_TOKEN"):
    c.JupyterHub.services.append(
        {
            "name": "grader",
            "url": "http://service:4010",
            "api_token": os.environ["GRADER_API_TOKEN"],
        }
    )
else:
    # Let JupyterHub auto-generate the token
    c.JupyterHub.services.append({"name": "grader", "url": "http://service:4010"})

c.JupyterHub.load_roles = [
    {
        "name": "grader-service",
        "scopes": ["admin:users", "read:users", "tokens", "admin:servers", "groups"],
        "services": ["grader"],
    }
]

c.JupyterHub.log_level = "INFO"
