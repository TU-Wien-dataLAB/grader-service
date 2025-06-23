import json
import os

from tornado.escape import json_decode
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from traitlets import Unicode

from grader_service.auth.auth import Authenticator
from grader_service.auth.login import LoginHandler, LogoutHandler
from grader_service.orm.api_token import APIToken


class JupyterHubTokenAuthenticator(Authenticator):
    user_info_url = Unicode(
        config=True,
        help="""The URL to where this authenticator makes a request to acquire user
        details with an access token received via jupyterhub.""",
    )

    http_client = AsyncHTTPClient()

    async def authenticate(self, handler, data):
        headers = {"Authorization": f"Bearer {data['token']}"}
        request = HTTPRequest(url=self.user_info_url, headers=headers, method="GET")

        response = await self.http_client.fetch(request=request)
        response = json_decode(response.body)
        username = response["name"]
        groups = response["groups"]

        return {"name": username, "groups": groups}

    def get_handlers(self, base_url):
        handlers = [
            (self.logout_url(base_url), LogoutHandler),
            (self.login_url(base_url), TokenLoginHandler),
        ]
        return handlers


class TokenLoginHandler(LoginHandler):
    async def post(self):
        data = json.loads(self.request.body)
        user = await self.login_user(data)

        if user:
            # create a API token for the user, that he can use to authenticate and return it
            token = APIToken.new(
                user=user,
                scopes=["identify"],  # Define the scopes for the token
                note="User login token",
                expires_in=os.environ.get("TOKEN_EXPIRES_IN", 1209600),  # Set expiration time
            )
            self.write({"api_token": token})
        else:
            html = await self._render(login_error="Invalid username or password")
            self.set_status(404)
            await self.finish(html)
