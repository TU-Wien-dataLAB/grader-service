# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

import datetime
import functools
import json
import os
import shlex
import shutil
import subprocess
import sys
import traceback
from http import HTTPStatus
from typing import Any, Awaitable, Callable, List, Optional

from traitlets import Type, Integer, TraitType, Unicode, Union, Bool
from traitlets import Callable as CallableTrait
from traitlets import List as ListTrait
from traitlets.config import SingletonConfigurable

from grader_service.api.models.base_model_ import Model
from grader_service.api.models.error_message import ErrorMessage
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
            if "/permissions" in self.request.path or "/config" in self.request.path:
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

    def __init__(
            self,
            application: GraderServer,
            request: httputil.HTTPServerRequest,
            **kwargs: Any,
    ) -> None:
        super().__init__(application, request, **kwargs)

        self.application: GraderServer = self.application  # add type hint for application
        self.log = self.application.log

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def prepare(self) -> Optional[Awaitable[None]]:
        if self.request.path.strip("/") != self.application.base_url.strip("/") and \
                self.request.path.strip("/") != self.application.base_url.strip("/") + "/health":
            authenticator = self.application.auth_cls(config=self.application.config)
            await authenticator.authenticate_user(self)
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
        if assignment is None or assignment.deleted == DeleteState.deleted or int(assignment.lectid) != int(lecture_id):
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Assignment with id " + str(assignment_id) + " was not found")
        return assignment

    def get_submission(self, lecture_id: int, assignment_id: int, submission_id: int) -> Submission:
        submission = self.session.query(Submission).get(submission_id)
        if (
                submission is None
                or submission.assignid != assignment_id
                or submission.assignment.lectid != lecture_id
        ):
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Submission was not found")
        return submission

    @property
    def gitbase(self):
        app: GraderServer = self.application
        return os.path.join(app.grader_service_dir, "git")

    def construct_git_dir(self, repo_type: str, lecture: Lecture, assignment: Assignment,
                          group_name: Optional[str] = None, submission: Optional[Submission] = None) -> Optional[str]:
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
                if repo_type == "autograde":
                    if submission is None or self.get_role(lecture.id).role < Scope.tutor:
                        raise HTTPError(403)
                    path = os.path.join(type_path, submission.username)
                else:
                    path = os.path.join(type_path, self.user.name)
            else:
                group = self.session.query(Group).get((self.user.name, lecture.id))
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
                ErrorMessage(status_code, error, self.request.path, reason, traceback=json.dumps(lines)).to_dict()))
        else:
            self.finish(json.dumps(ErrorMessage(status_code, error, self.request.path, reason).to_dict()))

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
                                    allow_none=False, config=True)

    # Git server file policy defaults
    git_max_file_size_mb = Integer(80, allow_none=False, config=True)
    git_max_file_count = Integer(512, allow_none=False, config=True)
    # empty list allows everything
    git_allowed_file_extensions = ListTrait(TraitType(Unicode), default_value=[], allow_none=False,
                                            config=True)

    enable_lti_features = Bool(False, config=True)
    lti_client_id = Unicode(None, config=True, allow_none=True)
    lti_token_url = Unicode(None, config=True, allow_none=True)
    # function used to change the hub username to the lti sourcedid value
    lti_username_convert = CallableTrait(None, config=True, allow_none=True, help="""
    Converts the grader service username to the lti sourced id.""")
    lti_token_private_key = Union(
        [Unicode(os.environ.get('LTI_PRIVATE_KEY', None)), CallableTrait(None)],
        allow_none=True,
        config=True,
        help="""
        Private Key used to encrypt bearer token request
        """,
    )
