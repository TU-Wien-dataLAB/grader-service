# Authentication & Authorization
To connect the Grader Service with JupyterHub, you need to configure authentication and authorization. This is crucial for managing user access and roles within the Grader Service, especially in educational settings where different users (instructors, tutors, students) have varying levels of access.

The Grader Service supports two distinct modes for handling authentication and authorization, designed to integrate with JupyterHub in educational environments. Each mode offers a different balance of simplicity and flexibility depending on your infrastructure and requirements.

In the Grader Service, users are associated with lectures and can hold one of the following roles:

- `instructor`
- `tutor`
- `student`

These roles determine access permissions within the app and are stored in the internal user model of the Grader Service.

## Mode 1: JupyterHub Provides API Token

In this simpler mode, **JupyterHub handles the user management**, and provides the user's API token to 
the Grader Service at server startup. 
The Grader Service then queries the JupyterHub API to obtain information about the current user (e.g., `username`, `groups`)
and stores this in its own database.

**Architecture Overview:**
![grader token auth architecture](../_static/assets/images/token-auth.svg "Token Authentication Architecture")

**Advantages:**

- Easy to set up and understand
- No need to manage additional OAuth flows

**Limitations:**

- Works only with **one JupyterHub instance**
- The Grader Service can only access information that JupyterHub exposes (e.g., groups)
- Less flexible for multi-hub or cross-institutional setups

### Example Configuration

In this example, we will use the `DummyAuthenticator` for simplicity, but you can replace it with any other authenticator that suits your needs.
Furthermore, Grader Service will use JupyterHub groups (e.g., `lect1:instructor`, `lect1:student`, `lect1:tutor`) to manage user roles.

First we will start with the JupyterHub configuration. This is typically done in the `jupyterhub_config.py` file.
:::{warning}
The following configuration is an example and should be adapted to your specific needs.
Make sure to replace the URLs and client credentials with your own values.
Also, ensure that encryption is enabled by the presence of the `JUPYTERHUB_CRYPT_KEY` environment variable, which should be a hex-encoded 32-byte key.
Otherwise, the `enable_auth_state` option will not work as expected.
:::

```python
# jupyterhub_config.py

## authenticator
from jupyterhub.auth import DummyAuthenticator
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.escape import json_encode, json_decode

c.JupyterHub.authenticator_class = DummyAuthenticator
c.Authenticator.allowed_users = {'admin', 'instructor', 'tutor', 'student'}
c.Authenticator.admin_users = {"admin"}
c.JupyterHub.load_groups = {"lect1:instructor": {'users' : ["admin", "instructor"]}, "lect1:student": {'users' : ["student"]}, "lect1:tutor": {'users' : ["tutor"]}}
c.Authenticator.enable_auth_state = True

# this hook will be called when a user starts a server and will pass the JupyterHub API token to the Grader Service
# in return the Grader Service will return an API token that can be used to authenticate with the Grader Service
async def pre_spawn_hook(spawner):
    http_client = AsyncHTTPClient()
    data = {"token" : spawner.api_token}
    request = HTTPRequest(url="<grader-service-url>/services/grader/login", method='POST', body=json_encode(data))

    response = await http_client.fetch(request=request)
    grader_api_token = json_decode(response.body)["api_token"]
    spawner.environment.update({"GRADER_API_TOKEN": grader_api_token})

c.Spawner.pre_spawn_hook = pre_spawn_hook
```

Next, we will configure the Grader Service to use the JupyterHub API token for authentication. This is typically done in the `grader_service_config.py` file.
Grader Service only needs JupyterHub's user information endpoint to fetch user details and roles.
After the user is authenticated, the Grader Service can be configured to create or update the user and their roles in its own database using the `post_auth_hook` function.
```python
# grader_service_config.py
from grader_service.auth.token import JupyterHubTokenAuthenticator

c.GraderService.authenticator_class = JupyterHubTokenAuthenticator
c.Authenticator.allow_all = True
c.JupyterHubTokenAuthenticator.user_info_url = "<jupyterhub-url>/hub/api/user"

def post_auth_hook(authenticator: Authenticator, handler: BaseHandler, authentication: dict):
    log = handler.log
    session = handler.session
    groups: list[str] = authentication["groups"]

    username = authentication["name"]
    user_model: User = session.query(User).filter(User.name == username).one_or_none()
    if user_model is None:
        user_model = User()
        user_model.name = username
        user_model.display_name = username
        session.add(user_model)
        session.commit()
    
    for group in groups:
        if (":" in group):
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

            role = session.query(Role).filter(Role.user_id == user.id, Role.lectid == lecture.id).one_or_none()
            if role is None:
                log.info(f'No role for user {username} in lecture {lecture_code}... creating role')
                role = Role(user_id=user.id, lectid=lecture.id, role=scope)
                session.add(role)
                session.commit()
            else:
                log.info(f'Found role {role.role.name} for user {username} in lecture {lecture_code}... updating role to {scope.name}')
                role.role = scope
                session.commit()
        else:
            log.info("Found group that doesn't match schema. Ignoring %s", group)        

    return authentication

c.Authenticator.post_auth_hook = post_auth_hook
```

## Mode 2: Grader Service Wraps JupyterHub

In this configuration, the Grader Service acts as the **primary authentication gateway**, handling authentication via  its own authenticator. It acts as a OAuth2 provider for JupyterHub instances and authenticates to them using **OAuth2**.

**Architecture Overview:**
![grader token auth architecture](../_static/assets/images/oauth-setup.svg "Token Authentication Architecture")

**Advantages:**

- Centralized user authentication across **multiple JupyterHub deployments**
- Fine-grained control over user roles and access in the Grader Service
- Can enrich user records with external data (e.g., institutional systems)

**Considerations:**

- More complex setup
- Requires configuring both the Grader Service and JupyterHub for OAuth2 communication

---
### Example Configuration
Just like in the previous example, we will use the `DummyAuthenticator` for simplicity, but you can replace it with any other authenticator that suits your needs.
Here, the Grader Service will act as an OAuth2 provider for JupyterHub, and will use its own user management system to handle user roles.
```python
# grader_service_config.py

from grader_service.auth.dummy import DummyAuthenticator

c.GraderService.authenticator_class = DummyAuthenticator
# default users
c.Authenticator.allowed_users = {'admin', 'instructor', 'student', 'tutor'}
c.Authenticator.admin_users = {'admin'}
# default roles
c.GraderService.load_roles = {"lect1": [{"members": ["admin", "instructor"], "role": "instructor"},
                                        {"members": ["tutor"], "role": "tutor"},
                                        {"members": ["student"], "role": "student"}]}

# JupyterHub client config
c.GraderService.oauth_clients = [{
    'client_id': '<my_id>',
    'client_secret': '<my_secret>',
    'redirect_uri': '<jupyterhub-url>/hub/oauth_callback'
}]
```

:::{warning}
The following configuration is an example and should be adapted to your specific needs.
Make sure to replace the URLs and client credentials with your own values.
Also, ensure that encryption is enabled by the presence of the `JUPYTERHUB_CRYPT_KEY` environment variable, which should be a hex-encoded 32-byte key.
Otherwise, the `enable_auth_state` option will not work as expected.
:::

Lastly, we will configure the JupyterHub to use the Grader Service as an OAuth2 provider.
After the user is authenticated, the Grader Service will provide an API token that can be used to authenticate with the Grader Service.
```python
# jupyterhub_config.py

## authenticator
from oauthenticator.generic import GenericOAuthenticator

c.JupyterHub.authenticator_class = GenericOAuthenticator
c.GenericOAuthenticator.oauth_callback_url = "<jupyterhub-url>/hub/oauth_callback"

c.GenericOAuthenticator.client_id = "<my_id>"
c.GenericOAuthenticator.client_secret = "<my_secret>"
c.GenericOAuthenticator.authorize_url = "<grader-service-url>/services/grader/api/oauth2/authorize"
c.GenericOAuthenticator.token_url = "<grader-service-url>/services/grader/api/oauth2/token"
c.GenericOAuthenticator.logout_redirect_url = "<grader-service-url>/services/grader/logout"

c.GenericOAuthenticator.userdata_url = "<grader-service-url>/services/grader/api/user"
c.GenericOAuthenticator.username_claim = "name"
c.Authenticator.enable_auth_state = True

def auth_state_hook(spawner, auth_state):
    token = auth_state["access_token"]

    # The environment variable GRADER_API_TOKEN is used by the labextension
    # to identify the user in API calls to the Grader Service.
    spawner.environment.update({"GRADER_API_TOKEN": token})


# We have access to the authentication data, which we can use to set
# `userdata` in the spawner of the user.
c.Spawner.auth_state_hook = auth_state_hook
```
