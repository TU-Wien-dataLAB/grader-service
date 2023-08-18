# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import asyncio
import shlex
import subprocess
import datetime
import functools
import json
import os
import shutil
import sys
import time
import traceback
import uuid
from _decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional

from traitlets import Type, Integer, TraitType, Unicode, Union, Bool
from traitlets import Callable as CallableTrait
from traitlets import List as ListTrait
from traitlets.config import SingletonConfigurable

from grader_service.api.models.base_model_ import Model
from grader_service.api.models.error_message import ErrorMessage
from grader_service.utils import maybe_future
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.orm import Group, Assignment, Submission
from grader_service.orm.base import Serializable, DeleteState
from grader_service.orm.lecture import Lecture
from grader_service.orm.takepart import Role, Scope
from grader_service.orm.user import User
from grader_service.registry import VersionSpecifier, register_handler
from grader_service.server import GraderServer
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from tornado import httputil, web
from tornado.escape import json_decode
from tornado.web import HTTPError
from tornado_sqlalchemy import SessionMixin

SESSION_COOKIE_NAME = 'grader-session-id'


def authorize(scopes: List[Scope]):
    """Checks if user is authorized.
    :param scopes: the user's roles
    :return: wrapper function
    """
    if not set(scopes).issubset({Scope.student, Scope.tutor,
                                 Scope.instructor}):
        return ValueError("Invalid scopes")

    def wrapper(handler_method):
        @functools.wraps(handler_method)
        async def request_handler_wrapper(self: "GraderBaseHandler", *args,
                                          **kwargs):
            lect_id = self.path_kwargs.get("lecture_id", None)
            if (("/permissions" in self.request.path)
                    or ("/config" in self.request.path)):
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
                    raise HTTPError(404, "Lecture not found")
                except json.decoder.JSONDecodeError:
                    raise HTTPError(403)
            elif (
                    lect_id is None
                    and "/lectures" in self.request.path
                    and self.request.method == "GET"
            ):
                return await handler_method(self, *args, **kwargs)

            role = self.session.query(Role).get((self.user.name, lect_id))
            if (role is None) or (role.role not in scopes):
                msg = f"User {self.user.name} tried to access "
                msg += f"{self.request.path} with insufficient privileges"
                self.log.warn(msg)
                raise HTTPError(403)
            return await handler_method(self, *args, **kwargs)

        return request_handler_wrapper

    return wrapper


class BaseHandler(SessionMixin, web.RequestHandler):
    """Base class of all handler classes

    Implements validation and request functions"""

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def __init__(
            self,
            application: GraderServer,
            request: httputil.HTTPServerRequest,
            **kwargs: Any,
    ) -> None:
        super().__init__(application, request, **kwargs)
        # add type hint for application
        self.application: GraderServer = self.application
        self.authenticator = self.application.authenticator
        self.log = self.application.log

    @property
    def user(self) -> User:
        return self.current_user

    def _set_cookie(self, key, value, encrypted=True, expires_days=1.0, **overrides):
        """Setting any cookie should go through here

        if encrypted use tornado's set_secure_cookie,
        otherwise set plaintext cookies.
        """
        # tornado <4.2 have a bug that consider secure==True as soon as
        # 'secure' kwarg is passed to set_secure_cookie
        kwargs = {}
        kwargs.update(self.settings.get('cookie_options', {}))
        kwargs.update(overrides)
        kwargs.update({'httponly': True})
        if self.request.protocol == 'https':
            kwargs['secure'] = True

        if encrypted:
            set_cookie = self.set_secure_cookie
        else:
            set_cookie = self.set_cookie

        self.log.debug("Setting cookie %s: %s", key, kwargs)
        set_cookie(key, value, expires_days=expires_days, **kwargs)

    def _set_user_cookie(self, user, server):
        self.log.debug("Setting cookie for %s: %s", user.name,
                       server.cookie_name)
        self._set_cookie(
            server.cookie_name, user.cookie_id, encrypted=True,
            path=server.base_url
        )

    def get_session_cookie(self):
        """Get the session id from a cookie

        Returns None if no session id is stored
        """
        return self.get_cookie(SESSION_COOKIE_NAME, None)

    def set_session_cookie(self):
        """Set a new session id cookie

        new session id is returned

        Session id cookie is *not* encrypted,
        so other services on this domain can read it.
        """
        session_id = uuid.uuid4().hex
        self._set_cookie(
            SESSION_COOKIE_NAME, session_id, encrypted=False,
            path=self.application.base_url
        )
        return session_id

    def set_grader_cookie(self, user):
        """set the login cookie for the Grader"""
        self._set_user_cookie(user, self.hub)

    def set_login_cookie(self, user):
        """Set login cookies for the Hub and single-user server."""

        if not self.get_session_cookie():
            self.set_session_cookie()

    def authenticate(self, data):
        return maybe_future(
            self.authenticator.get_authenticated_user(self, data))

    async def auth_to_user(self, authenticated, user=None):
        """Persist data from .authenticate() or .refresh_user() to the User database

        Args:
            authenticated(dict): return data from .authenticate or .refresh_user
            user(User, optional): the User object to refresh, if refreshing
        Return:
            user(User): the constructed User object
        """
        if isinstance(authenticated, str):
            authenticated = {'name': authenticated}
        username = authenticated['name']
        auth_state = authenticated.get('auth_state')
        admin = authenticated.get('admin')
        refreshing = user is not None

        if user and username != user.name:
            raise ValueError(
                f"Username doesn't match! {username} != {user.name}")

        user_model = self.session.query(User).get(username)
        if user_model is None:
            self.log.info(
                f'User {username} does not exist and will be created.')
            user_model = User()
            user_model.name = username
            self.session.add(user_model)
            self.session.commit()
        return user_model


    async def login_user(self, data=None):
        """Login a user"""
        # auth_timer = self.statsd.timer('login.authenticate').start()
        authenticated = await self.authenticate(data)
        # auth_timer.stop(send=False)

        if authenticated:
            user = await self.auth_to_user(authenticated)
            self.set_login_cookie(user)

            self.log.info("User logged in: %s", user.name)
            user._auth_refreshed = time.monotonic()
            return user
        else:
            self.log.warning(
                "Failed login for %s",
                (data or {}).get('username', 'unknown user')
            )

    @property
    def user(self) -> User:
        return self.current_user


class GraderBaseHandler(BaseHandler):

    async def prepare(self) -> Optional[Awaitable[None]]:
        if ((self.request.path.strip("/")
             != self.application.base_url.strip("/"))
                and (self.request.path.strip("/")
                     != self.application.base_url.strip("/") + "/health")):
            app_config = self.application.config
            # await self.authenticator.authenticate(self, self.request.body)
        return super().prepare()

    def validate_parameters(self, *args):
        if len(self.request.arguments) == 0:
            return
        unknown_args = set(self.request.query_arguments.keys()) - set(args)
        if len(unknown_args) != 0:
            raise HTTPError(400, reason=f"Unknown arguments: {unknown_args}")

    def get_role(self, lecture_id: int) -> Role:
        role = self.session.query(Role).get((self.user.name, lecture_id))
        if role is None:
            raise HTTPError(403)
        return role

    def get_assignment(self, lecture_id: int,
                       assignment_id: int) -> Assignment:
        assignment = self.session.query(Assignment).get(assignment_id)
        if ((assignment is None) or (assignment.deleted == DeleteState.deleted)
                or (int(assignment.lectid) != int(lecture_id))):
            msg = "Assignment with id " + str(assignment_id) + " was not found"
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason=msg)
        return assignment

    def get_submission(self, lecture_id: int, assignment_id: int,
                       submission_id: int) -> Submission:
        submission = self.session.query(Submission).get(submission_id)
        if (
                submission is None
                or submission.assignid != assignment_id
                or submission.assignment.lectid != lecture_id
        ):
            raise HTTPError(HTTPStatus.NOT_FOUND,
                            reason="Submission was not found")
        return submission

    @property
    def gitbase(self):
        app: GraderServer = self.application
        return os.path.join(app.grader_service_dir, "git")

    def construct_git_dir(self, repo_type: str, lecture: Lecture,
                          assignment: Assignment,
                          group_name: Optional[str] = None,
                          submission: Optional[Submission] = None
                          ) -> Optional[str]:
        """Helper method for every handler that needs to access git
        directories which returns the path of the repository based on
        the inputs or None if the repo_type is not recognized."""
        # TODO: refactor
        assignment_path = os.path.abspath(
            os.path.join(self.gitbase, lecture.code, str(assignment.id))
        )
        allowed_types = set(["source", "release", "edit"])
        if (repo_type in allowed_types):
            path = os.path.join(assignment_path, repo_type)
            if repo_type == "edit":
                path = os.path.join(path, str(submission.id))
                self.log.info(path)
        elif repo_type in ["autograde", "feedback"]:
            type_path = os.path.join(assignment_path, repo_type,
                                     assignment.type)
            if assignment.type == "user":
                if repo_type == "autograde":
                    if ((submission is None)
                            or (self.get_role(lecture.id).role < Scope.tutor)):
                        raise HTTPError(403)
                    path = os.path.join(type_path, submission.username)
                else:
                    path = os.path.join(type_path, self.user.name)
            else:
                group = self.session.query(Group).get((self.user.name,
                                                       lecture.id))
                if group is None:
                    raise HTTPError(404, reason="User is not in a group")
                path = os.path.join(type_path, group.name)
        elif repo_type == "user":
            user_path = os.path.join(assignment_path, repo_type)
            path = os.path.join(user_path, self.user.name)
        elif repo_type == "group":
            if group_name is None:
                return None
            group = self.session.query(Group).get((group_name, lecture.id))
            if group is None:
                raise HTTPError(404, reason="User is not in a group")
            group_path = os.path.join(assignment_path, repo_type)
            path = os.path.join(group_path, group.name)
        else:
            return None

        return path

    @staticmethod
    def is_base_git_dir(path: str) -> bool:
        try:
            out = subprocess.run(["git", "rev-parse", "--is-bare-repository"],
                                 cwd=path, capture_output=True)
            is_git = ((out.returncode == 0)
                      and ("true" in out.stdout.decode("utf-8")))
        except FileNotFoundError:
            is_git = False
        return is_git

    def duplicate_release_repo(self, repo_path_release: str,
                               repo_path_user: str,
                               assignment: Assignment, message: str,
                               checkout_main: bool = False):
        tmp_path_base = Path(
            self.application.grader_service_dir,
            "tmp",
            assignment.lecture.code,
            str(assignment.id),
            str(self.user.name))

        # Deleting dir
        if os.path.exists(tmp_path_base):
            shutil.rmtree(tmp_path_base)

        os.makedirs(tmp_path_base, exist_ok=True)
        tmp_path_release = tmp_path_base.joinpath("release")
        tmp_path_user = tmp_path_base.joinpath(self.user.name)

        self.log.info(f"Duplicating release repository {repo_path_release}")
        self.log.info(f"Temporary path used for copying: {tmp_path_base}")

        try:
            self._run_command(f"git clone -b main '{repo_path_release}'",
                              cwd=tmp_path_base)
            if checkout_main:
                self._run_command(f"git clone '{repo_path_user}'",
                                  cwd=tmp_path_base)
                self._run_command("git checkout -b main", cwd=tmp_path_user)
            else:
                self._run_command(f"git clone -b main '{repo_path_user}'",
                                  cwd=tmp_path_base)

            msg = f"Copying repo from {tmp_path_release} to {tmp_path_user}"
            self.log.info(msg)
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            if (sys.version_info.major == 3) and (sys.version_info.minor >= 8):
                shutil.copytree(tmp_path_release, tmp_path_user,
                                ignore=ignore, dirs_exist_ok=True)
            else:
                for item in os.listdir(tmp_path_release):
                    s = os.path.join(tmp_path_release, item)
                    d = os.path.join(tmp_path_user, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, ignore=ignore)
                    else:
                        shutil.copy2(s, d)
            cmd = 'sh -c \'git add -A'
            cmd += f'&& git commit --allow-empty -m "{message}"\''
            self._run_command(cmd, tmp_path_user)
            self._run_command("git push -u origin main", tmp_path_user)
        finally:
            shutil.rmtree(tmp_path_base)

    def _run_command(self, command, cwd=None, capture_output=False):
        # TODO currently there a two run_command functions,
        #  because duplicate_release_repo does not work
        #  with the _run_command_async
        try:
            self.log.info(f"Running: {command}")
            ret = subprocess.run(shlex.split(command), check=True, cwd=cwd,
                                 capture_output=True)
            if capture_output:
                return str(ret.stdout, 'utf-8')
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise HTTPError(500, reason="Subprocess Error")
        except FileNotFoundError as e:
            self.log.error(e)
            raise HTTPError(404, reason="File not found")

    async def _run_command_async(self, command, cwd=None):
        """Starts a sub process and runs a cmd command

        Args:
            command str: command that is getting run.
            cwd (str, optional): states where the command is getting run.
                                 Defaults to None.

        Raises:
            GitError: returns appropriate git error"""
        self.log.info(f"Running: {command}")
        ret = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd)
        await ret.wait()

    def write_json(self, obj) -> None:
        self.set_header("Content-Type", "application/json")
        chunk = GraderBaseHandler._serialize(obj)
        self.write(json.dumps(chunk))

    def write_error(self, status_code: int, **kwargs) -> None:
        self.set_header('Content-Type', 'application/json')
        _, e, _ = kwargs.get("exc_info", (None, None, None))
        error = httputil.responses.get(status_code, "Unknown")
        reason = None
        if e and isinstance(e, HTTPError) and e.reason:
            reason = e.reason
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            self.finish(json.dumps(
                ErrorMessage(status_code, error, self.request.path, reason,
                             traceback=json.dumps(lines)).to_dict()))
        else:
            self.finish(json.dumps(ErrorMessage(status_code, error,
                                                self.request.path,
                                                reason).to_dict()))

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
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Model):
            return cls._serialize(obj.to_dict())
        return None


class LogoutHandler(BaseHandler):
    pass


def authenticated(
        method: Callable[..., Optional[Awaitable[None]]]
) -> Callable[..., Optional[Awaitable[None]]]:
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in `tornado.web.HTTPError`
    with code 403 will be raised.
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


def lti_username_convert(username):
    return username.replace("e", "")


@register_handler(r"\/", VersionSpecifier.V1)
class VersionHandlerV1(GraderBaseHandler):
    async def get(self):
        self.write("1.0")


class RequestHandlerConfig(SingletonConfigurable):
    """This class exists to not avoid all request handlers to inherit
    from traitlets.config.Configurable and making all requests super
    slow. If a request handler needs configurable values, they can be
    accessed from this object."""
    autograde_executor_class = Type(default_value=LocalAutogradeExecutor,
                                    # TODO: why does using
                                    # LocalAutogradeExecutor give
                                    # subclass error?
                                    klass=object,
                                    allow_none=False, config=True)

    # Git server file policy defaults
    git_max_file_size_mb = Integer(80, allow_none=False, config=True)
    git_max_file_count = Integer(512, allow_none=False, config=True)
    # empty list allows everything
    git_allowed_file_extensions = ListTrait(TraitType(Unicode),
                                            default_value=[],
                                            allow_none=False,
                                            config=True)

    enable_lti_features = Bool(False, config=True)
    lti_client_id = Unicode(None, config=True, allow_none=True)
    lti_token_url = Unicode(None, config=True, allow_none=True)
    # function used to change the hub username to the lti sourcedid value
    help_msg = "Converts the grader service username to the lti sourced id."
    lti_username_convert = CallableTrait(default_value=lti_username_convert,
                                         config=True,
                                         allow_none=True,
                                         help=help_msg)
    lti_token_private_key = Union(
        [Unicode(os.environ.get('LTI_PRIVATE_KEY', None)),
         CallableTrait(None)],
        allow_none=True,
        config=True,
        help="""
        Private Key used to encrypt bearer token request
        """,
    )
