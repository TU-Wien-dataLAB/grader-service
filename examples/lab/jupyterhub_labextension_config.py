import os
c.GitService.git_access_token = os.environ.get("JUPYTERHUB_API_TOKEN")
c.GitService.git_remote_url = "grader_service:4010/services/grader/git"
c.GitService.git_http_scheme = "http"
    
c.RequestService.port = 4010
c.RequestService.host = "grader_service"
c.RequestService.scheme = "http"

c.JupyterHub.services.append(
    {
        'name': 'grader',
        'url': 'http://grader_service:4010',
        'api_token': '7e272a9df62444de9d2d111b5ff6e70f'
    }
)

c.JupyterHub.load_groups ={
    "lect1:instructor": ["user1"],
    "lect1:tutor": ["user2"],
    "lect1:student": ["jovyan", "user3"]
    }
    