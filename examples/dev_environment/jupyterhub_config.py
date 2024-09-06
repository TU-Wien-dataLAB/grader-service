from jupyterhub import orm

## generic
c.JupyterHub.admin_access = True
c.Spawner.default_url = '/lab'
c.Spawner.cmd = ["jupyter-labhub"]

## authenticator
from oauthenticator.generic import GenericOAuthenticator

c.JupyterHub.authenticator_class = GenericOAuthenticator
c.GenericOAuthenticator.oauth_callback_url = "http://localhost:8080/hub/oauth_callback"

c.GenericOAuthenticator.client_id = "hub"
c.GenericOAuthenticator.client_secret = "hub"
c.GenericOAuthenticator.authorize_url = "http://localhost:4010/services/grader/api/oauth2/authorize"
c.GenericOAuthenticator.token_url = "http://localhost:4010/services/grader/api/oauth2/token"

c.GenericOAuthenticator.userdata_url = "http://localhost:4010/services/grader/api/user"
c.GenericOAuthenticator.username_claim = "name"

##############################
# PASS GRADER TOKEN TO SPAWNER


def post_auth_hook(authenticator, handler, authentication):
    db = authenticator.db
    log = authenticator.log
    username = authentication["name"]
    log.debug(f"{username=:}")
    log.debug(f'auth_state: {authentication["auth_state"]}')
    roles = authentication["auth_state"]["oauth_user"]["roles"]    
    for role in roles:
        lecture_code, lecture_role = role.split(':')
        
        group = orm.Group.find(db, role)
        if group is None:
            log.info(f"Creating group: '{role}'")
            group = orm.Group()
            group.name = role
            db.add(group)
            db.commit()
        
        user_model: orm.User = orm.User.find(db, username)
        if user_model not in group.users:
            log.info(f"Adding user to group: {group.name}")
            group.users.append(user_model)
            db.commit()

        
    return authentication
    

c.Authenticator.post_auth_hook = post_auth_hook

c.Authenticator.enable_auth_state = True


def userdata_hook(spawner, auth_state):
    token = auth_state["access_token"]

    # The environment variable GRADER_API_TOKEN is used by the lab-extension
    # to identify the user in API calls to the Grader Service.
    spawner.environment.update({"GRADER_API_TOKEN": token})


# We have access to the authentication data, which we can use to set
# `userdata` in the spawner of the user.
c.Spawner.auth_state_hook = userdata_hook

##############################

# c.Authenticator.allowed_users = {'instructor', 'tutor', 'student1', 'student2'}
c.Authenticator.allow_all = True
c.Authenticator.admin_users = ["admin"]

## spawner
c.JupyterHub.spawner_class = 'jupyterhub.spawner.SimpleLocalProcessSpawner'
c.SimpleLocalProcessSpawner.home_dir_template = '/tmp/lab_dir/{username}'

## simple setup
# c.JupyterHub.ip = '0.0.0.0' # proxy
c.JupyterHub.ip = '127.0.0.1'
c.JupyterHub.port = 8080

## setup with https
# c.JupyterHub.hub_ip = "192.168.5.145"
# c.JupyterHub.ip = '0.0.0.0' # proxy
# c.JupyterHub.port = 8080

# c.JupyterHub.ssl_key  = "jupyterhub_config/dl.key"
# c.JupyterHub.ssl_cert = "jupyterhub_config/__dl_hpc_tuwien_ac_at_cert.cer"


c.JupyterHub.services.append(
    {
        'name': 'grader',
        'url': 'http://127.0.0.1:4010',
        'api_token': '7572f93a2e7640999427d9289c8318c0'
    }
)

c.JupyterHub.log_level = "INFO"

## Is ignored -> actual config is in ~/.jupyter/jupyter_server_config.py
import os

c.GitService.git_access_token = os.environ.get("JUPYTERHUB_API_TOKEN")
c.GitService.git_remote_url = "127.0.0.1:4010/services/grader/git"
c.GitService.git_http_scheme = "http"