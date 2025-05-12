import json
import os
from urllib.parse import urlencode

from jinja2 import Template
from grader_service.auth.auth import Authenticator
from grader_service.auth.login import LogoutHandler
from grader_service.handlers.base_handler import BaseHandler
from tornado.escape import url_escape
from tornado.httputil import url_concat
from grader_service.auth.login import LoginHandler
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.escape import json_decode
from grader_service.auth.oauth2 import OAuthenticator
from traitlets import Unicode

from grader_service.orm.api_token import APIToken
class JupyterHubTokenAuthenticator(Authenticator):
    user_info_url = Unicode(
        config=True,
        help="""The URL to where this authenticator makes a request to acquire user
        details with an access token received via jupyterhub."""
    )

    http_client = AsyncHTTPClient()

    async def authenticate(self, handler, data):
        headers = {"Authorization" : f"Bearer {data["token"]}"}
        request = HTTPRequest(url=self.user_info_url, headers=headers, method='GET')

        response = await self.http_client.fetch(request=request)
        response = json_decode(response.body)
        username = response["name"]
        groups = response["groups"]

        return {"name" : username, "groups": groups}

    def get_handlers(self, base_url):
        return [(self.login_url(base_url), TokenLoginHandler)]
    

class TokenLoginHandler(LoginHandler):

    def _render(self, login_error=None, username=None):
        context = {
            "next": url_escape(self.get_argument('next', default='')),
            "username": username,
            "login_error": login_error,
            "login_url": self.settings['login_url'],
            "authenticator_login_url": url_concat(
                self.authenticator.login_url(self.application.base_url),
                {
                    'next': self.get_argument('next', ''),
                },
            ),
            "authenticator": self.authenticator,
            "xsrf": self.xsrf_token.decode('ascii'),
        }
        custom_html = Template(
            self.authenticator.get_custom_html(self.application.base_url)
        ).render(**context)
        return self.render_template(
            'auth/login.html.j2',
            **context,
            custom_html=custom_html,
        )
    
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
            html = await self._render(
                login_error='Invalid username or password', username=data['username']
            )
            await self.finish(html)

    
