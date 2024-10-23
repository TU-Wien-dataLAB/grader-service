# Authenticating the Lab-Extension

Without any configuration, the Grader Lab-Extension has no way to access the authentication information.
JupyterHub allows us to pass the `access_token` that we received during the OAuth flow with the Grader Service to the environment of the notebook server.
The Lab-Extension then uses this token in the environment variable `GRADER_API_TOKEN` to authenticate itself with the Grader Service. A sample configuration can be seen below:

```python
c.Authenticator.enable_auth_state = True


def userdata_hook(spawner, auth_state):
    token = auth_state["access_token"]

    # The environment variable GRADER_API_TOKEN is used by the lab-extension
    # to identify the user in API calls to the Grader Service.
    spawner.environment.update({"GRADER_API_TOKEN": token})


# We have access to the authentication data, which we can use to set
# `userdata` in the spawner of the user.
c.Spawner.auth_state_hook = userdata_hook
```