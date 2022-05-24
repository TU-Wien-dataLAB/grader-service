# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import base64
import datetime
import functools
import json
import logging
import os
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any, Awaitable, Callable, List, Optional
from urllib.parse import ParseResult, urlparse, quote

from traitlets import Type
from traitlets.config import SingletonConfigurable

from grader_service.api.models.base_model_ import Model
from grader_service.api.models.error_message import ErrorMessage
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.orm import Group, Assignment, Submission
from grader_service.orm.base import DeleteState, Serializable
from grader_service.orm.lecture import Lecture, LectureState
from grader_service.orm.takepart import Role, Scope
from grader_service.orm.user import User
from grader_service.registry import VersionSpecifier, register_handler
from grader_service.request import RequestService
from grader_service.server import GraderServer
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from tornado import httputil, web
from tornado.escape import json_decode
from tornado.httpclient import HTTPClientError
from tornado.web import HTTPError
from tornado_sqlalchemy import SessionMixin


def authorize(scopes: List[Scope]):
    """
    Checks if user is authorized.
    :param scopes: the user's roles
    :return: wrapper function
    """
    if not set(scopes).issubset({Scope.student, Scope.tutor, Scope.instructor}):
        return ValueError("Invalid scopes")

    # needs_auth = set(scopes) != {Scope.student, Scope.tutor, Scope.instructor}

    def wrapper(handler_method):
        @functools.wraps(handler_method)
        async def request_handler_wrapper(self: "GraderBaseHandler", *args, **kwargs):
            lect_id = self.path_kwargs.get("lecture_id", None)
            if "/permissions" in self.request.path:
                return await handler_method(self, *args, **kwargs)
            if (
                    lect_id is None
                    and "/lectures" in self.request.path
                    and self.request.method == "POST"
            ):
                # lecture name and semester is in post body
                try:
                    data = json_decode(self.request.body)
                    lect_id = (
                        self.session.query(Lecture)
                            .filter(Lecture.code == data["code"])
                            .one()
                            .id
                    )
                except MultipleResultsFound:
                    raise HTTPError(403)
                except NoResultFound:
                    raise HTTPError(404)
                except json.decoder.JSONDecodeError:
                    raise HTTPError(403)
            elif (
                    lect_id is None
                    and "/lectures" in self.request.path
                    and self.request.method == "GET"
            ):
                return await handler_method(self, *args, **kwargs)

            role = self.session.query(Role).get((self.user.name, lect_id))
            if role is None or not role.role in scopes:
                self.log.warn(
                    f"User {self.user.name} tried to access {self.request.path} with insufficient privileges"
                )
                raise HTTPError(403)
            return await handler_method(self, *args, **kwargs)

        return request_handler_wrapper

    return wrapper


class GraderBaseHandler(SessionMixin, web.RequestHandler):
    """
    Base class of all handler classes that implements validation and request functions
    """
    request_service = RequestService()
    hub_request_service = RequestService()

    def __init__(
            self,
            application: GraderServer,
            request: httputil.HTTPServerRequest,
            **kwargs: Any,
    ) -> None:
        super().__init__(application, request, **kwargs)

        self.application: GraderServer = (
            self.application
        )  # add type hint for application
        hub_api_parsed: ParseResult = urlparse(self.application.hub_api_url)
        self.hub_request_service.scheme = hub_api_parsed.scheme
        (
            self.hub_request_service.host,
            self.hub_request_service.port,
        ) = httputil.split_host_and_port(hub_api_parsed.netloc)
        self.hub_api_base_path: str = hub_api_parsed.path

        self.log = self.application.log

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def prepare(self) -> Optional[Awaitable[None]]:

        if self.request.path.strip("/") != self.application.base_url.strip("/"):
            await self.authenticate_user()
        return super().prepare()

    def validate_parameters(self, *args):
        if len(self.request.arguments) == 0:
            return
        unknown_arguments = set(self.request.query_arguments.keys()) - set(args)
        if len(unknown_arguments) != 0:
            raise HTTPError(400, reason=f"Unknown arguments: {unknown_arguments}")

    def get_role(self, lecture_id: int) -> Role:
        role = self.session.query(Role).get((self.user.name, lecture_id))
        if role is None:
            raise HTTPError(403)
        return role

    def get_assignment(self, lecture_id: int, assignment_id: int) -> Assignment:
        assignment = self.session.query(Assignment).get(assignment_id)
        if assignment is None or assignment.deleted == 1 or assignment.lectid != lecture_id:
            raise HTTPError(404)
        return assignment

    def get_submission(self, lecture_id: int, assignment_id: int, submission_id: int) -> Submission:
        submission = self.session.query(Submission).get(submission_id)
        if (
                submission is None
                or submission.assignid != assignment_id
                or submission.assignment.lectid != lecture_id
        ):
            raise HTTPError(404)
        return submission

    @property
    def gitbase(self):
        app: GraderServer = self.application
        return os.path.join(app.grader_service_dir, "git")

    def construct_git_dir(self, repo_type: str, lecture: Lecture, assignment: Assignment,
                          group_name: Optional[str] = None) -> Optional[str]:
        """Helper method for every handler that needs to access git directories which returns
        the path of the repository based on the inputs or None if the repo_type is not recognized.
        """
        assignment_path = os.path.abspath(
            os.path.join(self.gitbase, lecture.code, str(assignment.id))
        )
        if repo_type == "source" or repo_type == "release":
            path = os.path.join(assignment_path, repo_type)
        elif repo_type in ["autograde", "feedback"]:
            type_path = os.path.join(assignment_path, repo_type, assignment.type)
            if assignment.type == "user":
                path = os.path.join(type_path, self.user.name)
            else:
                group = self.session.query(Group).get((self.user.name, lecture.id))
                if group is None:
                    raise HTTPError(404)
                path = os.path.join(type_path, group.name)
        elif repo_type == "user":
            user_path = os.path.join(assignment_path, repo_type)
            path = os.path.join(user_path, self.user.name)
        elif repo_type == "group":
            if group_name is None:
                return None
            group = self.session.query(Group).get((group_name, lecture.id))
            if group is None:
                raise HTTPError(404)
            group_path = os.path.join(assignment_path, repo_type)
            path = os.path.join(group_path, group.name)
        else:
            return None

        return path

    @staticmethod
    def is_base_git_dir(path: str) -> bool:
        try:
            out = subprocess.run(["git", "rev-parse", "--is-bare-repository"], cwd=path, capture_output=True)
            is_git = out.returncode == 0 and "true" in out.stdout.decode("utf-8")
        except FileNotFoundError:
            is_git = False
        return is_git

    def duplicate_release_repo(self, repo_path_release: str, repo_path_user: str, assignment: Assignment, message: str,
                               checkout_main: bool = False):
        tmp_path_base = os.path.join(self.application.grader_service_dir, "tmp", assignment.lecture.code,
                                     str(assignment.id), self.user.name)
        # Deleting dir
        if os.path.exists(tmp_path_base):
            shutil.rmtree(tmp_path_base)

        os.makedirs(tmp_path_base, exist_ok=True)
        tmp_path_release = os.path.join(tmp_path_base, "release")
        tmp_path_user = os.path.join(tmp_path_base, self.user.name)

        self.log.info(f"Duplicating release repository {repo_path_release}")
        self.log.info(f"Temporary path used for copying: {tmp_path_base}")

        try:
            self._run_command(f"git clone -b main '{repo_path_release}'", cwd=tmp_path_base)
            if checkout_main:
                self._run_command(f"git clone '{repo_path_user}'", cwd=tmp_path_base)
                self._run_command(f"git checkout -b main", cwd=tmp_path_user)
            else:
                self._run_command(f"git clone -b main '{repo_path_user}'", cwd=tmp_path_base)

            self.log.info(f"Copying repository contents from {tmp_path_release} to {tmp_path_user}")
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            if sys.version_info.major == 3 and sys.version_info.minor >= 8:
                shutil.copytree(tmp_path_release, tmp_path_user, ignore=ignore, dirs_exist_ok=True)
            else:
                for item in os.listdir(tmp_path_release):
                    s = os.path.join(tmp_path_release, item)
                    d = os.path.join(tmp_path_user, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, ignore=ignore)
                    else:
                        shutil.copy2(s, d)

            self._run_command(f'sh -c \'git add -A && git commit --allow-empty -m "{message}"\'', tmp_path_user)
            self._run_command("git push -u origin main", tmp_path_user)
        finally:
            shutil.rmtree(tmp_path_base)

    def _run_command(self, command, cwd=None, capture_output=False):
        """Starts a sub process and runs an cmd command

        Args:
            command str: command that is getting run.
            cwd (str, optional): states where the command is getting run. Defaults to None.
            capture_output (bool, optional): states if output is getting saved. Defaults to False.

        Raises:
            GitError: returns appropriate git error 

        Returns:
            str: command output
        """
        try:
            self.log.info(f"Running: {command}")
            ret = subprocess.run(shlex.split(command), check=True, cwd=cwd, capture_output=True)
            if capture_output:
                return str(ret.stdout, 'utf-8')
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise HTTPError(500)
        except FileNotFoundError as e:
            self.log.error(e)
            raise HTTPError(404)

    async def authenticate_user(self):
        """
        This is a workaround for async authentication. `get_current_user` cannot be asynchronous and a request cannot be made in a blocking manner.
        This sets the `current_user` property before each request before being checked by the `authenticated` decorator.
        """
        token = self.get_request_token()
        if token is None:
            self.write_error(401)
            await self.finish()
            return

        start_time = time.monotonic()

        user = await self.authenticate_token_user(token)
        if user is None:
            self.log.warn("Request from unauthenticated user")
            self.write_error(403)
            await self.finish()
            return
        self.set_secure_cookie(token, json.dumps(user), expires_days=self.application.max_token_cookie_age_days)
        self.log.info(
            f'User {user["name"]} has been authenticated (took {(time.monotonic() - start_time) * 1e3:.2f}ms)')

        user_model = self.session.query(User).get(user["name"])
        if user_model is None:
            self.log.info(f'User {user["name"]} does not exist and will be created.')
            user_model = User(name=user["name"])
            self.session.add(user_model)
            self.session.commit()

        # user is authenticated by the cookie and the user exists in the database
        if self.authenticate_cookie_user(user):
            self.current_user = user_model
            return

        lecture_roles = {
            code: {"role": role}
            for code, role in [tuple(g.split(":", 1)) for g in user["groups"]]
        }

        for lecture_code in lecture_roles.keys():
            lecture = (
                self.session.query(Lecture)
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
                self.session.add(lecture)
        self.session.commit()

        self.session.query(Role).filter(Role.username == user["name"]).delete()
        for lecture_code, obj in lecture_roles.items():
            lecture = (
                self.session.query(Lecture)
                    .filter(Lecture.code == lecture_code)
                    .one_or_none()
            )
            if lecture is None:
                raise HTTPError(500, f"Could not find lecture with code: {lecture_code}. Inconsistent database state!")
            role = Role()
            role.username = user["name"]
            role.lectid = lecture.id
            role.role = obj["role"]
            self.session.add(role)
        self.session.commit()

        self.current_user = user_model

    async def authenticate_token_user(self, token: str) -> Optional[dict]:
        max_token_age = self.application.max_token_cookie_age_days
        token_user = self.get_secure_cookie(token, max_age_days=max_token_age)
        if not token_user:
            user = await self.get_current_user_async(token)
            return user
        else:
            return json.loads(token_user)

    def authenticate_cookie_user(self, user: dict) -> bool:
        max_age = self.application.max_user_cookie_age_days
        cookie_user = self.get_secure_cookie(quote(user["name"]), max_age_days=max_age)
        if not cookie_user:
            self.set_secure_cookie(quote(user["name"]), json.dumps(user), expires_days=max_age)
            return False
        else:
            equal = user == json.loads(cookie_user)
            if not equal:
                self.set_secure_cookie(
                    quote(user["name"]), json.dumps(user), expires_days=max_age
                )
            return equal

    def get_request_token(self) -> Optional[str]:
        for (k, v) in sorted(self.request.headers.get_all()):
            if k == "Authorization":
                name, value = v.split(" ")
                if name == "Token":
                    token = value
                elif name == "Basic":
                    auth_decoded = base64.decodebytes(value.encode("ascii")).decode(
                        "ascii"
                    )
                    _, token = auth_decoded.split(
                        ":", 2
                    )  # we interpret the password as the token and ignore the username
                else:
                    token = None
                return token

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
            logging.getLogger(str(self.__class__)).error(e.reason)
            return None
        except HTTPClientError as e:
            logging.getLogger(str(self.__class__)).error(e.response.error)
            return None
        except KeyError:
            return None
        return user

    def write_json(self, obj) -> None:
        self.set_header("Content-Type", "application/json")
        chunk = GraderBaseHandler._serialize(obj)
        self.write(json.dumps(chunk))

    def write_error(self, status_code: int, **kwargs) -> None:
        self.clear()
        self.set_status(status_code)
        _, e, _ = kwargs.get("exc_info", (None, None, None))
        if e and isinstance(e, HTTPError) and e.reason:
            self.write_json(ErrorMessage(e.reason))
        else:
            msg = httputil.responses.get(status_code, "Unknown")
            self.write_json(ErrorMessage(msg))

    @classmethod
    def _serialize(cls, obj: object):
        if isinstance(obj, list):
            return [cls._serialize(o) for o in obj]
        if isinstance(obj, dict):
            return {k: cls._serialize(v) for k, v in obj.items()}
        if isinstance(obj, tuple):
            return tuple(cls._serialize(o) for o in obj)
        if isinstance(obj, Serializable):
            return cls._serialize(obj.serialize())
        if isinstance(obj, (str, int, float, complex)) or obj is None:
            return obj
        if isinstance(obj, datetime.datetime):
            return str(obj)
        if isinstance(obj, Model):
            return cls._serialize(obj.to_dict())
        return None

    @property
    def user(self) -> User:
        return self.current_user


def authenticated(
        method: Callable[..., Optional[Awaitable[None]]]
) -> Callable[..., Optional[Awaitable[None]]]:
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in, an `tornado.web.HTTPError` with cod 403 will be raised.
    """

    @functools.wraps(method)
    def wrapper(  # type: ignore
            self: GraderBaseHandler, *args, **kwargs
    ) -> Optional[Awaitable[None]]:
        if not self.current_user:
            raise HTTPError(403)
        return method(self, *args, **kwargs)

    return wrapper


@register_handler(r"\/", VersionSpecifier.NONE)
class VersionHandler(GraderBaseHandler):
    async def get(self):
        self.write("1.0")


@register_handler(r"\/", VersionSpecifier.V1)
class VersionHandlerV1(GraderBaseHandler):
    async def get(self):
        self.write("1.0")


# This class exists to not avoid all request handlers to inherit from traitlets.config.Configurable
# and making all requests super slow. If a request handler needs configurable values, they can be accessed
# from this object.
class RequestHandlerConfig(SingletonConfigurable):
    autograde_executor_class = Type(default_value=LocalAutogradeExecutor,
                                    klass=object,  # TODO: why does using LocalAutogradeExecutor give subclass error?
                                    allow_none=False).tag(config=True)
