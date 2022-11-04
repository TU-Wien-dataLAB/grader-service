import base64
import json
import time
from typing import Dict, Tuple, Union, Optional, Type
from urllib.parse import quote

from traitlets import Bool, Integer
from traitlets.config import LoggingConfigurable

from grader_service.handlers.base_handler import GraderBaseHandler
from grader_service.orm import User, Lecture, Role
from grader_service.orm.base import DeleteState
from grader_service.orm.lecture import LectureState
from tornado.web import HTTPError

from grader_service.orm.takepart import Scope


class Authenticator(LoggingConfigurable):
    use_cookies = Bool(True, help="Whether to store cookies when authenticating users.", config=True, allow_none=False)
    max_user_cookie_age_minutes = Integer(15, help="Time in minutes until a user cookie expires.", config=True,
                                          allow_none=False)
    max_token_cookie_age_minutes = Integer(5, help="Time in minutes until a token cookie expires.", config=True,
                                           allow_none=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def authenticate_user(self, handler: GraderBaseHandler) -> None:
        """
        Authenticates a user by setting the ``current_user`` property of the request handler based on the request.
        Adds the necessary user roles for the user.

        :param handler: A tornado request handler with an active sqlalchemy session.
        :return: None
        """
        start_time = time.monotonic()
        user, lecture_roles = await self.get_user(handler)
        self.log.info(f'User {user.name} has been authenticated (took {(time.monotonic() - start_time) * 1e3:.2f}ms)')

        if self.get_cookie(handler, user.name, minutes_valid=self.max_user_cookie_age_minutes) is None:
            self.set_lecture_roles(handler, user, lecture_roles)
        handler.current_user = user

    async def get_user(self, handler: GraderBaseHandler) -> Tuple[User, Dict[str, Dict[str, str]]]:
        """
        Retrieves a user based on the request from an authentication provider and
        builds the lecture roles based on the authentication result.

        The lecture roles have to be of the format:
        {
            "<lecture_code>": {"role": "<role>"},
            ...
        }

        :param handler: A tornado request handler with an active sqlalchemy session.
        :return: A tuple of the user and the lecture roles the user should have.
        """
        raise NotImplementedError("Implement in subclass!")

    def set_lecture_roles(self, handler: GraderBaseHandler, user: User, lecture_roles: Dict[str, Dict[str, str]]):
        for lecture_code in lecture_roles.keys():
            lecture = (
                handler.session.query(Lecture)
                    .filter(Lecture.code == lecture_code)
                    .one_or_none()
            )
            if lecture is None:  # create lecture if no lecture with that name exists yet (code is set in create)
                self.log.info(f"Adding new lecture with lecture_code {lecture_code}")
                lecture = Lecture()
                lecture.code = lecture_code
                lecture.name = lecture_code
                lecture.state = LectureState.active
                lecture.deleted = DeleteState.active
                handler.session.add(lecture)
        handler.session.commit()

        handler.session.query(Role).filter(Role.username == user.name).delete()
        for lecture_code, obj in lecture_roles.items():
            lecture = (
                handler.session.query(Lecture)
                    .filter(Lecture.code == lecture_code)
                    .one_or_none()
            )
            if lecture is None:
                raise HTTPError(500, f"Could not find lecture with code: {lecture_code}. Inconsistent database state!")
            scopes = [role.name for role in Scope]
            if obj["role"] in scopes:
                role = Role()
                role.username = user.name
                role.lectid = lecture.id
                role.role = obj["role"]
                handler.session.add(role)
        handler.session.commit()

    def get_or_create_user_model(self, handler: GraderBaseHandler, user_name: str) -> User:
        user_model = handler.session.query(User).get(user_name)
        if user_model is None:
            self.log.info(f'User {user_name} does not exist and will be created.')
            user_model = User()
            user_model.name = user_name
            handler.session.add(user_model)
            handler.session.commit()
        return user_model

    def set_cookie(self, handler: GraderBaseHandler, name: str, data: Union[str, dict], minutes_valid: float) -> None:
        """
        Sets a cookie and takes care of quoting and encoding.

        :param handler: The request handler used to store the cookie.
        :param name: The name of the cookie to store.
        :param data: The data to store in the cookie. Can be string or dict.
        :param minutes_valid: Duration in minutes that the cookie is valid.
        :return: None
        """
        if not self.use_cookies:
            return
        expires_days = minutes_valid / 1440
        if isinstance(data, dict):
            data = json.dumps(data)
        handler.set_secure_cookie(quote(name), data, expires_days=expires_days)

    def get_cookie(self, handler: GraderBaseHandler, name: str, minutes_valid: float, decode=False) -> Union[str, dict, None]:
        """
        Get a cookie stored in the handler. Takes care of quoting and decoding the data.

        :param handler: The request handler used to store the cookie.
        :param name: The name of the cookie to retrieve.
        :param minutes_valid: Duration in minutes that the cookie is valid.
        :param decode: Whether to decode the data using json.
        :return: The data as string or dict or None.
        """
        if not self.use_cookies:
            return None
        expires_days = minutes_valid / 1440
        data = handler.get_secure_cookie(quote(name), max_age_days=expires_days)
        if data is None:
            return None
        if decode:
            return json.loads(data)
        else:
            return data.decode("utf-8")


class TokenAuthenticator(Authenticator):
    """
    Base class for authenticator that use tokens in request for authentication.
    Also supports basic auth but ignores username and interprets the password as a token!
    """
    async def get_user(self, handler: GraderBaseHandler) -> Tuple[User, Dict[str, Dict[str, str]]]:
        raise NotImplementedError("Implement in subclass!")

    def get_request_token(self, handler: GraderBaseHandler) -> str:
        token = self._get_request_token(handler)
        if token is None:
            raise HTTPError(401)
        return token

    @staticmethod
    def _get_request_token(handler: GraderBaseHandler) -> Optional[str]:
        for (k, v) in sorted(handler.request.headers.get_all()):
            if k == "Authorization":
                name, value = v.split(" ")
                if name == "Token":
                    token = value
                elif name == "Basic":
                    auth_decoded = base64.decodebytes(value.encode("ascii")).decode("ascii")
                    # we interpret the password as the token and ignore the username
                    _, token = auth_decoded.split(":", 2)
                else:
                    token = None
                return token
