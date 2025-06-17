import os

## generic
c.JupyterHub.admin_access = True
c.Spawner.default_url = "/lab"
c.Spawner.cmd = ["jupyter-labhub"]

## authenticator
from oauthenticator.generic import GenericOAuthenticator

c.JupyterHub.authenticator_class = GenericOAuthenticator
c.GenericOAuthenticator.oauth_callback_url = "http://localhost:8080/hub/oauth_callback"

c.GenericOAuthenticator.client_id = "my_id"
c.GenericOAuthenticator.client_secret = "my_secret"
c.GenericOAuthenticator.authorize_url = "http://localhost:4010/services/grader/api/oauth2/authorize"
c.GenericOAuthenticator.token_url = "http://localhost:4010/services/grader/api/oauth2/token"
c.GenericOAuthenticator.logout_redirect_url = "http://localhost:4010/services/grader/logout"

c.GenericOAuthenticator.userdata_url = "http://localhost:4010/services/grader/api/user"
c.GenericOAuthenticator.username_claim = "name"
c.Authenticator.enable_auth_state = True

##############################
# PASS GRADER TOKEN TO SPAWNER


def auth_state_hook(spawner, auth_state):
    token = auth_state["access_token"]

    # The environment variable GRADER_API_TOKEN is used by the lab-extension
    # to identify the user in API calls to the Grader Service.
    spawner.environment.update({"GRADER_API_TOKEN": token})


# We have access to the authentication data, which we can use to set
# `userdata` in the spawner of the user.
c.Spawner.auth_state_hook = auth_state_hook

##############################

c.Authenticator.allowed_users = {"admin", "instructor", "tutor", "student"}
c.Authenticator.admin_users = {"admin"}

## spawner
c.JupyterHub.spawner_class = "jupyterhub.spawner.SimpleLocalProcessSpawner"
c.SimpleLocalProcessSpawner.home_dir_template = os.path.join(os.getcwd(), "home_dir", "{username}")

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
