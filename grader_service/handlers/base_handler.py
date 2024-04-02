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
from _decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional

from traitlets import Type, Integer, TraitType, Unicode
from traitlets import List as ListTrait
from traitlets.config import SingletonConfigurable

from grader_service.api.models.base_model_ import Model
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


class GraderBaseHandler(SessionMixin, web.RequestHandler):
    """Base class of all handler classes

    Implements validation and request functions"""

    def __init__(
            self,
            application: GraderServer,
            request: httputil.HTTPServerRequest,
            **kwargs: Any,
    ) -> None:
        super().__init__(application, request, **kwargs)
        # add type hint for application
        self.application: GraderServer = self.application
        self.log = self.application.log

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    async def prepare(self) -> Optional[Awaitable[None]]:
        if ((self.request.path.strip("/")
             != self.application.base_url.strip("/"))
            and (self.request.path.strip("/")
                 != self.application.base_url.strip("/") + "/health")):
            app_config = self.application.config
            authenticator = self.application.auth_cls(config=app_config)
            await authenticator.authenticate_user(self)
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

    @property
    def user(self) -> User:
        return self.current_user


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

    
