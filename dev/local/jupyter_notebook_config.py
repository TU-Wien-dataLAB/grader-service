import os

c.GitService.git_access_token = os.environ.get("JUPYTERHUB_API_TOKEN")
c.GitService.git_remote_url = "http://127.0.0.1:4010/git"
