import json
import os
from typing import Tuple, Dict, Optional
from urllib.parse import urlparse, ParseResult

from tornado.httpclient import HTTPClientError
from tornado.web import HTTPError
from traitlets import Unicode

from grader_service.auth.base import TokenAuthenticator
from grader_service.handlers.base_handler import GraderBaseHandler
from grader_service.orm import User
from grader_service.request import RequestService


class JupyterHubGroupAuthenticator(TokenAuthenticator):
    hub_api_url = Unicode(os.environ.get("JUPYTERHUB_API_URL"), allow_none=False).tag(config=True)

    group_separator = Unicode(":",
                              help="Separator for splitting lecture codes and user roles in JupyterHub group name.",
                              allow_none=False, config=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        hub_api_parsed: ParseResult = urlparse(self.hub_api_url)
        self.hub_request_service = RequestService(url=f"{hub_api_parsed.scheme}://{hub_api_parsed.netloc}")
        self.hub_api_base_path: str = hub_api_parsed.path

    async def get_user(self, handler: GraderBaseHandler) -> Tuple[User, Dict[str, Dict[str, str]]]:
        token = self.get_request_token(handler)

        user = await self.authenticate_token_user(handler, token)
        if user is None:
            self.log.warn("Request from unauthenticated user")
            raise HTTPError(403)
        self.set_cookie(handler, token, user, minutes_valid=self.max_token_cookie_age_minutes)

        user_model = self.get_or_create_user_model(handler, user["name"])

        lecture_roles = {
            code: {"role": role}
            for code, role in
            (t for t in (tuple(g.split(self.group_separator, 1)) for g in user["groups"]) if len(t) == 2)
        }

        return user_model, lecture_roles

    async def authenticate_token_user(self, handler: GraderBaseHandler, token: str) -> Optional[dict]:
        token_user = self.get_cookie(handler, token, minutes_valid=self.max_token_cookie_age_minutes)
        if not token_user:
            user = await self.get_current_user_async(token)
        else:
            user = json.loads(token_user)

        return user

    def authenticate_cookie_user(self, handler: GraderBaseHandler, user: dict) -> bool:
        cookie_user = self.get_cookie(handler, user["name"], minutes_valid=self.max_user_cookie_age_minutes)
        if not cookie_user:
            self.set_cookie(handler, user["name"], user, minutes_valid=self.max_user_cookie_age_minutes)
            return False
        else:
            equal = user == json.loads(cookie_user)
            if not equal:
                self.set_cookie(handler, user["name"], user, minutes_valid=self.max_user_cookie_age_minutes)
            return equal

    async def get_current_user_async(self, token) -> Optional[dict]:
        try:
            user: dict = await self.hub_request_service.request(
                "GET",
                self.hub_api_base_path + f"/user",
                header={"Authorization": f"token {token}"},
            )
            if user["kind"] != "user":
                return None
        except HTTPError as e:
            self.log.error(e.reason)
            return None
        except HTTPClientError as e:
            self.log.error(e.response.error)
            return None
        except ConnectionRefusedError:
            self.log.error(f"Could not connect to the JupyterHub at {self.hub_api_url}! "
                           f"Is the URL correct and is it running?")
            return None
        except KeyError:
            return None
        return user
