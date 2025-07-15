# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import asyncio
import base64
import datetime
import functools
import json
import os
import re
import shlex
import shutil
import subprocess
import time
import uuid
from _decimal import Decimal
from http import HTTPStatus
from pathlib import Path
from typing import Any, Awaitable, Callable, List, Optional, Union
from urllib.parse import parse_qsl, urlparse

from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm.session import Session
from tornado import httputil, web
from tornado.escape import json_decode
from tornado.httputil import url_concat
from tornado.web import HTTPError
from traitlets import Integer, TraitType, Type, Unicode
from traitlets import List as ListTrait
from traitlets.config import SingletonConfigurable

from grader_service import __version__
from grader_service.api.models.base_model import Model
from grader_service.autograding.local_grader import LocalAutogradeExecutor
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import APIToken, Assignment, Submission
from grader_service.orm.base import DeleteState, Serializable
from grader_service.orm.lecture import Lecture
from grader_service.orm.takepart import Role, Scope
from grader_service.orm.user import User
from grader_service.registry import VersionSpecifier, register_handler
from grader_service.server import GraderServer
from grader_service.utils import get_browser_protocol, maybe_future, url_path_join, utcnow

SESSION_COOKIE_NAME = "grader-session-id"

auth_header_pat = re.compile(r"^(token|bearer|basic)\s+([^\s]+)$", flags=re.IGNORECASE)


def check_authorization(
    self: "GraderBaseHandler", scopes: list[Scope], lecture_id: Union[int, None]
) -> bool:
    if ("/permissions" in self.request.path) or ("/config" in self.request.path):
        return True
    if lecture_id is None and "/lectures" in self.request.path and self.request.method == "POST":
        # lecture name and semester is in post body
        try:
            data = json_decode(self.request.body)
            lecture_id = self.session.query(Lecture).filter(Lecture.code == data["code"]).one().id
        except MultipleResultsFound:
            raise HTTPError(403)
        except NoResultFound:
            raise HTTPError(404, reason="Lecture not found")
        except json.decoder.JSONDecodeError:
            raise HTTPError(403)
    elif lecture_id is None and "/lectures" in self.request.path and self.request.method == "GET":
        return True

    role = self.session.get(Role, (self.user.name, lecture_id))
    if (role is None) or (role.role not in scopes):
        msg = f"User {self.user.name} tried to access "
        msg += f"{self.request.path} with insufficient privileges"
        self.log.warning(msg)
        raise HTTPError(403)
    return True


def authorize(scopes: list[Scope]):
    """Checks if user is authorized.
    :param scopes: the user's roles
    :return: wrapper function
    """
    if not set(scopes).issubset({Scope.student, Scope.tutor, Scope.instructor}):
        return ValueError("Invalid scopes")

    def wrapper(handler_method):
        @functools.wraps(handler_method)
        async def request_handler_wrapper(self: "GraderBaseHandler", *args, **kwargs):
            lecture_id = self.path_kwargs.get("lecture_id", None)
            check_authorization(
                self, scopes, lecture_id
            )  # raises appropriate HTTPError if not authorized
            return await handler_method(self, *args, **kwargs)

        return request_handler_wrapper

    return wrapper


class BaseHandler(web.RequestHandler):
    """Base class of all handler classes

    Implements validation and request functions"""

    def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
        pass

    def __init__(
        self, application: GraderServer, request: httputil.HTTPServerRequest, **kwargs: Any
    ) -> None:
        super().__init__(application, request, **kwargs)
        # add type hint for application
        self._accept_cookie_auth = True
        self._accept_token_auth = True

        self.application: GraderServer = self.application
        self.authenticator = self.application.authenticator
        self.log = self.application.log

    async def prepare(self) -> Optional[Awaitable[None]]:
        # strip trailing slash
        self.request.path = self.request.path.rstrip("/")

        # start session
        self.session: Session = self.application.session_maker()

        # authenticate
        try:
            await self.get_current_user()

            # if user is not authenticated and is not actively trying to authenticate
            if not self.current_user and self.request.path not in [
                self.settings["login_url"],
                self.application.base_url.rstrip("/"),
                url_path_join(self.application.base_url, "/health"),
                url_path_join(self.application.base_url, "/api/oauth2/token"),
                url_path_join(self.application.base_url, "/oauth_callback"),
                url_path_join(self.application.base_url, "/lti13/oauth_callback"),
            ]:
                # require git to authenticate with token -> otherwise return 401 code
                # by default, git sends the request unauthenticated, first
                if self.request.path.startswith(url_path_join(self.application.base_url, "/git")):
                    self.set_status(401)
                    self.set_header("WWW-Authenticate", 'Basic realm="Git Repository"')
                    self.finish("Unauthenticated Git request, Authentication required")
                    return

                # send to login page if ui page request
                if self.request.path in [
                    url_path_join(self.application.base_url, "/api/oauth2/authorize")
                ] or self.request.path.startswith(url_path_join(self.application.base_url, "/ui")):
                    url = url_concat(self.settings["login_url"], dict(next=self.request.uri))
                    self.redirect(url)
                    return

                if self.request.headers.get("Authorization") is None:
                    raise HTTPError(401, reason="No API token in auth header")

                # do not redirect to login page if we hit api endpoints
                raise HTTPError(401, reason="API Token is invalid or expired.")

        except Exception as e:
            # ensure get_current_user is never called again for this handler,
            # since it failed
            self._grader_user = None
            self.log.exception("Failed to get current user")
            if isinstance(e, SQLAlchemyError):
                self.log.error("Rolling back session due to database error")
                self.session.rollback()
            if isinstance(e, HTTPError) and e.status_code == 401:
                raise e
        await maybe_future(super().prepare())
        return

    @property
    def oauth_provider(self):
        return self.application.oauth_provider

    @property
    def csp_report_uri(self):
        return self.settings.get(
            "csp_report_uri", url_path_join(self.application.base_url, "security/csp-report")
        )

    @property
    def content_security_policy(self):
        """The default Content-Security-Policy header

        Can be overridden by defining Content-Security-Policy in settings['headers']
        """
        return "; ".join(["frame-ancestors 'self'", "report-uri " + self.csp_report_uri])

    def _set_cookie(self, key, value, encrypted=True, **overrides):
        """Setting any cookie should go through here

        if encrypted use tornado's set_secure_cookie,
        otherwise set plaintext cookies.
        """
        # tornado <4.2 have a bug that consider secure==True as soon as
        # 'secure' kwarg is passed to set_secure_cookie
        kwargs = {"httponly": True}
        public_url = self.settings.get("public_url")
        if public_url:
            if public_url.scheme == "https":
                kwargs["secure"] = True
        else:
            if self.request.protocol == "https":
                kwargs["secure"] = True

        kwargs.update(self.settings.get("cookie_options", {}))
        kwargs.update(overrides)

        if key.startswith("__Host-"):
            # __Host- cookies must be secure and on /
            kwargs["path"] = "/"
            kwargs["secure"] = True

        if encrypted:
            set_cookie = self.set_secure_cookie
        else:
            set_cookie = self.set_cookie

        self.log.debug("Setting cookie %s: %s", key, kwargs)
        set_cookie(key, value, **kwargs)

    def _set_user_cookie(self, user, server: "GraderServer"):
        self.log.debug("Setting cookie for %s: %s", user.name, server.cookie_name)
        self._set_cookie(
            server.cookie_name, user.cookie_id, encrypted=True, path=server.base_url.rstrip("/")
        )

    def clear_login_cookies(self):
        kwargs = {}
        user = self.get_current_user_cookie()
        session_id = self.get_session_cookie()
        if session_id:
            # clear session id
            session_cookie_kwargs = {}
            session_cookie_kwargs.update(kwargs)

            self.clear_cookie(
                SESSION_COOKIE_NAME,
                path=self.application.base_url.rstrip("/"),
                **session_cookie_kwargs,
            )

            if user:
                # user is logged in, clear any tokens associated with the current session
                # don't clear session tokens if not logged in,
                # because that could be a malicious logout request!
                count = 0
                for access_token in self.session.query(APIToken).filter_by(
                    username=user.name, session_id=session_id
                ):
                    self.session.delete(access_token)
                    count += 1
                if count:
                    self.log.debug("Deleted %s access tokens for %s", count, user.name)
                    self.session.commit()

        # clear hub cookie
        self.clear_cookie(
            self.application.cookie_name, path=self.application.base_url.rstrip("/"), **kwargs
        )

    def get_session_cookie(self):
        """Get the session id from a cookie

        Returns None if no session id is stored
        """
        return self.get_cookie(SESSION_COOKIE_NAME, None)

    def _user_for_cookie(self, cookie_name, cookie_value=None):
        """Get the User for a given cookie, if there is one"""
        cookie_id = self.get_secure_cookie(
            cookie_name, cookie_value, max_age_days=self.application.cookie_max_age_days
        )

        def clear():
            self.clear_cookie(cookie_name, path=self.application.base_url.rstrip("/"))

        if cookie_id is None:
            if self.get_cookie(cookie_name):
                self.log.warning("Invalid or expired cookie token")
                clear()
            return
        cookie_id = cookie_id.decode("utf8", "replace")
        user = self.session.query(User).filter(User.cookie_id == cookie_id).first()
        # user = self._user_from_orm(u)
        if user is None:
            self.log.warning("Invalid cookie token")
            # have cookie, but it's not valid. Clear it and start over.
            clear()
            return
        # TODO: update user activity
        # if self._record_activity(user):
        #     self.session.commit()
        return user

    def _record_activity(self, obj, timestamp=None):
        """record activity on an ORM object

        If last_activity was more recent than self.activity_resolution seconds ago,
        do nothing to avoid unnecessarily frequent database commits.

        Args:
            obj: an ORM object with a last_activity attribute
            timestamp (datetime, optional): the timestamp of activity to register.
        Returns:
            recorded (bool): True if activity was recorded, False if not.
        """
        if timestamp is None:
            timestamp = utcnow(with_tz=False)
        resolution = self.settings.get("activity_resolution", 0)
        if not obj.last_activity or resolution == 0:
            self.log.debug("Recording first activity for %s", obj)
            obj.last_activity = timestamp
            return True
        if (timestamp - obj.last_activity).total_seconds() > resolution:
            # this debug line will happen just too often
            # uncomment to debug last_activity updates
            # self.log.debug("Recording activity for %s", obj)
            obj.last_activity = timestamp
            return True
        return False

    def get_auth_token(self):
        """Get the authorization token from Authorization header"""
        auth_header = self.request.headers.get("Authorization", "")
        match = auth_header_pat.match(auth_header)
        if not match:
            return None

        if match.group(1).lower() == "basic":
            auth_decoded = base64.b64decode(match.group(2)).decode("ascii")
            _, token = auth_decoded.split(":", 2)
            return token
        else:
            return match.group(2)

    @functools.lru_cache
    def get_token(self):
        """get token from authorization header"""
        token = self.get_auth_token()
        if token is None:
            return None
        orm_token = APIToken.find(self.session, token)
        return orm_token

    def get_current_user_token(self):
        """get_current_user from Authorization header token"""
        # record token activity
        orm_token = self.get_token()
        if orm_token is None:
            return None
        now = utcnow(with_tz=False)
        recorded = self._record_activity(orm_token, now)
        if recorded:
            self.session.commit()

        # record that we've been token-authenticated
        # XSRF checks are skipped when using token auth
        self._token_authenticated = True
        return orm_token.user

    def get_current_user_cookie(self):
        """get_current_user from a cookie token"""
        return self._user_for_cookie(self.application.cookie_name)

    async def refresh_auth(self, user, force=False):
        """Refresh user authentication info

        Calls `authenticator.refresh_user(user)`

        Called at most once per user per request.

        Args:
            user (User): the user whose auth info is to be refreshed
            force (bool): force a refresh instead of checking last refresh time
        Returns:
            user (User): the user having been refreshed,
                or None if the user must login again to refresh auth info.
        """
        refresh_age = self.authenticator.auth_refresh_age
        if not refresh_age:
            return user
        now = time.monotonic()
        if not force and user._auth_refreshed and (now - user._auth_refreshed < refresh_age):
            # auth up-to-date
            return user

        # refresh a user at most once per request
        if not hasattr(self, "_refreshed_users"):
            self._refreshed_users = set()
        if user.name in self._refreshed_users:
            # already refreshed during this request
            return user
        self._refreshed_users.add(user.name)

        self.log.debug("Refreshing auth for %s", user.name)
        auth_info = await self.authenticator.refresh_user(user, self)

        if not auth_info:
            self.log.warning(
                "User %s has stale auth info. Login is required to refresh.", user.name
            )
            return

        user._auth_refreshed = now

        if auth_info:
            # refresh_user confirmed that it's up-to-date,
            # nothing to refresh
            return user

        # Ensure name field is set. It cannot be updated.
        auth_info["name"] = user.name

        if "auth_state" not in auth_info:
            # refresh didn't specify auth_state,
            # so preserve previous value to avoid clearing it
            auth_info["auth_state"] = await user.get_auth_state()
        return await self.auth_to_user(auth_info, user)

    async def get_current_user(self):
        """get current username"""
        if not hasattr(self, "_grader_user"):
            user = None
            try:
                if self._accept_token_auth:
                    user = self.get_current_user_token()
                if user is None and self._accept_cookie_auth:
                    user = self.get_current_user_cookie()
                if user and isinstance(user, User):
                    user = await self.refresh_auth(user)
                self._grader_user = user
            except Exception:
                # don't let errors here raise more than once
                self._grader_user = None
                # but still raise, which will get handled in .prepare()
                raise
        return self._grader_user

    def on_finish(self):
        self.session.close()

    @property
    def current_user(self) -> User:
        """Override .current_user accessor from tornado

        Allows .get_current_user to be async.
        """
        if not hasattr(self, "_grader_user"):
            raise RuntimeError("Must call async get_current_user first!")
        return self._grader_user

    @property
    def user(self) -> User:
        return self.current_user

    def set_session_cookie(self):
        """Set a new session id cookie

        new session id is returned

        Session id cookie is *not* encrypted,
        so other services on this domain can read it.
        """
        session_id = uuid.uuid4().hex
        self._set_cookie(
            SESSION_COOKIE_NAME,
            session_id,
            encrypted=False,
            path=self.application.base_url.rstrip("/"),
        )
        return session_id

    def set_grader_cookie(self, user):
        """set the login cookie for the Hub"""
        self._set_user_cookie(user, self.application)

    def set_login_cookie(self, user):
        """Set login cookies for the Hub and single-user server."""

        if not self.get_session_cookie():
            self.set_session_cookie()

        # create and set a new cookie for the hub
        cookie_user = self.get_current_user_cookie()
        if cookie_user is None or cookie_user.name != user.name:
            if cookie_user:
                self.log.info(f"User {cookie_user.name} is logging in as {user.name}")
            self.set_grader_cookie(user)

        # make sure xsrf cookie is updated
        # this avoids needing a second request to set the right xsrf cookie
        self._grader_user = user
        # _set_xsrf_cookie(
        #     self, self._xsrf_token_id, cookie_path=self.application.base_url, authenticated=True
        # )

    def authenticate(self, data):
        return maybe_future(self.authenticator.get_authenticated_user(self, data))

    async def auth_to_user(self, authenticated, user=None):
        """Persist data from .authenticate() or .refresh_user() to the User database

        Args:
            authenticated(dict): return data from .authenticate or .refresh_user
            user(User, optional): the User object to refresh, if refreshing
        Return:
            user(User): the constructed User object
        """
        if isinstance(authenticated, str):
            authenticated = {"name": authenticated}
        username = authenticated["name"]
        auth_state = authenticated.get("auth_state")

        if user and username != user.name:
            raise ValueError(f"Username doesn't match! {username} != {user.name}")

        user_model = self.session.get(User, username)
        if user_model is None:
            self.log.info(f"User {username} does not exist and will be created.")
            user_model = User()
            user_model.name = username
            self.session.add(user_model)
            self.session.commit()

        # apply authenticator-managed groups
        if self.authenticator.manage_groups:
            if "groups" not in authenticated:
                # to use manage_groups, group membership must always be specified
                # Authenticators that don't support this feature will omit it,
                # which should fail here rather than silently not implement the requested behavior
                auth_cls = self.authenticator.__class__.__name__
                raise ValueError(
                    f"Authenticator.manage_groups is enabled, but auth_model for {username} specifies no groups."
                    f" Does {auth_cls} support manage_groups=True?"
                )
            group_names = authenticated["groups"]
            if group_names is not None:
                user.sync_groups(group_names)
        # apply authenticator-managed roles
        if self.authenticator.manage_roles:
            auth_roles = authenticated.get("roles")
            if auth_roles is not None:
                user.sync_roles(auth_roles)

        # always set auth_state and commit,
        # because there could be key-rotation or clearing of previous values
        # going on.
        if not self.authenticator.enable_auth_state:
            # auth_state is not enabled. Force None.
            auth_state = None

        await user_model.save_auth_state(auth_state)
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
            self.log.warning("Failed login for %s", (data or {}).get("username", "unknown user"))

    def get_template(self, name, sync=False):
        """
        Return the jinja template object for a given name

        If sync is True, we return a Template that is compiled without async support.
        Only those can be used in synchronous code.

        If sync is False, we return a Template that is compiled with async support
        """
        if sync:
            return self.application.jinja_env_sync.get_template(name)
        else:
            return self.application.jinja_env.get_template(name)

    def render_template(self, name, sync=False, **ns):
        """
        Render jinja2 template

        If sync is set to True, we render the template & return a string
        If sync is set to False, we return an awaitable
        """
        template_ns = {}
        template_ns.update(self.template_namespace)
        template_ns["xsrf_token"] = self.xsrf_token.decode("ascii")
        template_ns.update(ns)
        template = self.get_template(name, sync)
        if sync:
            return template.render(**template_ns)
        else:
            return template.render_async(**template_ns)

    @property
    def parsed_scopes(self) -> set:
        # TODO: if user is admin, the scopes should contain "admin-ui" for login.html template
        scopes = set()
        return scopes

    @property
    def template_namespace(self):
        user = self.current_user
        base_url = os.path.join(self.application.base_url, "")  # make sure "/" is at the end
        ns = dict(
            base_url=base_url,
            prefix=base_url,
            user=user,
            login_url=self.settings["login_url"],
            login_service=self.authenticator.login_service,
            logout_url=self.settings["logout_url"],
            static_url=self.static_url,
            version_hash="",
            parsed_scopes=self.parsed_scopes,
            xsrf=self.xsrf_token.decode("ascii"),
        )
        if self.application.template_vars:
            for key, value in self.application.template_vars.items():
                if callable(value):
                    value = value(user)
                ns[key] = value
        return ns

    def _validate_next_url(self, next_url):
        """Validate next_url handling

        protects against external redirects, etc.

        Returns empty string if next_url is not considered safe,
        resulting in same behavior as if next_url is not specified.
        """
        # protect against some browsers' buggy handling of backslash as slash
        next_url = next_url.replace("\\", "%5C")
        public_url = self.settings.get("public_url")
        if public_url:
            proto = public_url.scheme
            host = public_url.netloc
        else:
            # guess from request
            proto = get_browser_protocol(self.request)
            host = self.request.host

        if next_url.startswith("///"):
            # strip more than 2 leading // down to 2
            # because urlparse treats that as empty netloc,
            # whereas browsers treat more than two leading // the same as //,
            # so netloc is the first non-/ bit
            next_url = "//" + next_url.lstrip("/")
        parsed_next_url = urlparse(next_url)

        if (next_url + "/").startswith((f"{proto}://{host}/", f"//{host}/")):
            # treat absolute URLs for our host as absolute paths:
            # below, redirects that aren't strictly paths are rejected
            next_url = parsed_next_url.path
            if parsed_next_url.query:
                next_url = next_url + "?" + parsed_next_url.query
            if parsed_next_url.fragment:
                next_url = next_url + "#" + parsed_next_url.fragment
            parsed_next_url = urlparse(next_url)

        # if it still has host info, it didn't match our above check for *this* host
        if next_url and (parsed_next_url.netloc or not next_url.startswith("/")):
            self.log.warning("Disallowing redirect outside JupyterHub: %r", next_url)
            next_url = ""

        return next_url

    def get_next_url(self, user=None, default=None):
        """Get the next_url for login redirect

        Default URL after login:

        - if redirect_to_server (default): send to user's own server
        - else: /hub/home
        """
        next_url = self.get_argument("next", default="")
        next_url = self._validate_next_url(next_url)

        # this is where we know if next_url is coming from ?next= param or we are using a default url
        if next_url:
            next_url_from_param = True
        else:
            next_url_from_param = False

        if not next_url:
            # custom default URL, usually passed because user landed on that page but was not logged in
            if default:
                next_url = default
            else:
                # As set in jupyterhub_config.py
                if callable(self.authenticator.login_redirect_url):
                    next_url = self.authenticator.login_redirect_url(self)
                else:
                    next_url = url_path_join(
                        self.application.base_url, self.authenticator.login_redirect_url
                    )

        if not next_url_from_param:
            # when a request made with ?next=... assume all the params have already been encoded
            # otherwise, preserve params from the current request across the redirect
            next_url = self.append_query_parameters(next_url, exclude=["next", "_xsrf"])
        return next_url

    def append_query_parameters(self, url, exclude=None):
        """Append the current request's query parameters to the given URL.

        Supports an extra optional parameter ``exclude`` that when provided must
        contain a list of parameters to be ignored, i.e. these parameters will
        not be added to the URL.

        This is important to avoid infinite loops with the next parameter being
        added over and over, for instance.

        The default value for ``exclude`` is an array with "next". This is useful
        as most use cases in JupyterHub (all?) won't want to include the next
        parameter twice (the next parameter is added elsewhere to the query
        parameters).

        :param str url: a URL
        :param list exclude: optional list of parameters to be ignored, defaults to
        a list with "next" (to avoid redirect-loops)
        :rtype (str)
        """
        if exclude is None:
            exclude = ["next"]
        if self.request.query:
            query_string = [
                param for param in parse_qsl(self.request.query) if param[0] not in exclude
            ]
            if query_string:
                url = url_concat(url, query_string)
        return url


class GraderBaseHandler(BaseHandler):
    def validate_parameters(self, *args):
        if len(self.request.arguments) == 0:
            return
        unknown_args = set(self.request.query_arguments.keys()) - set(args)
        if len(unknown_args) != 0:
            raise HTTPError(400, reason=f"Unknown arguments: {unknown_args}")

    def write_error(self, status_code, **kwargs):
        self.log.error("Error %s: %s", status_code, self._reason)
        return super().write_error(status_code, **kwargs)

    def get_role(self, lecture_id: int) -> Role:
        role = self.session.get(Role, (self.user.name, lecture_id))
        if role is None:
            raise HTTPError(403)
        return role

    def get_lecture(self, lecture_id: int) -> Lecture:
        lecture: Lecture = self.session.get(Lecture, lecture_id)
        return lecture

    def get_assignment(self, lecture_id: int, assignment_id: int) -> Assignment:
        assignment: Assignment = self.session.get(Assignment, assignment_id)
        if (
            (assignment is None)
            or (assignment.deleted == DeleteState.deleted)
            or (int(assignment.lectid) != int(lecture_id))
        ):
            msg = "Assignment with id " + str(assignment_id) + " was not found"
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=msg)
        return assignment

    def get_submission(self, lecture_id: int, assignment_id: int, submission_id: int) -> Submission:
        submission = self.session.get(Submission, submission_id)
        if (
            (submission is None)
            or (submission.assignid != assignment_id)
            or (int(submission.assignment.lectid) != int(lecture_id))
            or (submission.deleted == DeleteState.deleted)
        ):
            msg = "Submission with id " + str(submission_id) + " was not found"
            raise HTTPError(HTTPStatus.NOT_FOUND, reason=msg)
        return submission

    def get_latest_submissions(
        self, assignment_id, must_have_feedback=False, username=None
    ) -> List[Submission]:
        query = (
            self.session.query(Submission.username, func.max(Submission.date).label("max_date"))
            .filter(Submission.assignid == assignment_id)
            .filter(Submission.deleted == DeleteState.active)
            .group_by(Submission.username)
        )

        if must_have_feedback:
            query = query.filter(Submission.feedback_status != "not_generated")

        if username:
            query = query.filter(Submission.username == username)

        subquery = query.subquery()

        # Build the main query
        submissions = (
            self.session.query(Submission)
            .options(joinedload(Submission.user))
            .join(
                subquery,
                (Submission.username == subquery.c.username)
                & (Submission.date == subquery.c.max_date)
                & (Submission.assignid == assignment_id)
                & (Submission.deleted == DeleteState.active),
            )
            .order_by(Submission.id)
            .all()
        )

        return submissions

    def get_all_submissions(self, assignment_id) -> List[Submission]:
        query = (
            self.session.query(Submission)
            .options(joinedload(Submission.user))
            .filter(Submission.assignid == assignment_id)
            .filter(Submission.deleted == DeleteState.active)
        )
        return query.all()

    def get_best_submissions(
        self, assignment_id, must_have_feedback=False, username=None
    ) -> List[Submission]:
        query = (
            self.session.query(Submission.username, func.max(Submission.score).label("max_score"))
            .filter(Submission.assignid == assignment_id)
            .filter(Submission.deleted == DeleteState.active)
            .group_by(Submission.username)
        )

        if must_have_feedback:
            query = query.filter(Submission.feedback_status != "not_generated")

        if username:
            query = query.filter(Submission.username == username)

        subquery = query.subquery()

        # Build the main query
        submissions = (
            self.session.query(Submission)
            .options(joinedload(Submission.user))
            .join(
                subquery,
                (Submission.username == subquery.c.username)
                & (Submission.score == subquery.c.max_score)
                & (Submission.assignid == assignment_id)
                & (Submission.deleted == DeleteState.active),
            )
            .order_by(Submission.id)
            .all()
        )
        return submissions

    @property
    def gitbase(self):
        app: GraderServer = self.application
        return os.path.join(app.grader_service_dir, "git")

    def construct_git_dir(
        self,
        repo_type: GitRepoType,
        lecture: Lecture,
        assignment: Assignment,
        submission: Optional[Submission] = None,
    ) -> Optional[str]:
        """Helper method for every handler that needs to access git
        directories which returns the path of the repository based on
        the inputs or None if the repo_type is not recognized."""
        # TODO: refactor
        assignment_path = os.path.abspath(
            os.path.join(self.gitbase, lecture.code, str(assignment.id))
        )
        allowed_types = {GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.EDIT}
        if repo_type in allowed_types:
            path = os.path.join(assignment_path, repo_type)
            if repo_type == GitRepoType.EDIT:
                path = os.path.join(path, str(submission.id))
                self.log.info(path)
        elif repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK}:
            type_path = os.path.join(assignment_path, repo_type, "user")
            if repo_type == GitRepoType.AUTOGRADE:
                if (submission is None) or (self.get_role(lecture.id).role < Scope.tutor):
                    raise HTTPError(403)
                path = os.path.join(type_path, submission.username)
            else:
                path = os.path.join(type_path, self.user.name)
        elif repo_type == GitRepoType.USER:
            user_path = os.path.join(assignment_path, repo_type)
            path = os.path.join(user_path, self.user.name)
        else:
            raise HTTPError(400, reason=f"Unknown repo type: {repo_type}")

        return path

    @staticmethod
    def is_base_git_dir(path: str) -> bool:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--is-bare-repository"], cwd=path, capture_output=True
            )
            is_git = (out.returncode == 0) and ("true" in out.stdout.decode("utf-8"))
        except FileNotFoundError:
            is_git = False
        return is_git

    def duplicate_release_repo(
        self,
        repo_path_release: str,
        repo_path_user: str,
        assignment: Assignment,
        message: str,
        checkout_main: bool = False,
    ):
        tmp_path_base = Path(
            self.application.grader_service_dir,
            "tmp",
            assignment.lecture.code,
            str(assignment.id),
            str(self.user.name),
        )

        # Deleting dir
        if os.path.exists(tmp_path_base):
            shutil.rmtree(tmp_path_base)

        os.makedirs(tmp_path_base, exist_ok=True)
        tmp_path_release = tmp_path_base.joinpath("release")
        tmp_path_user = tmp_path_base.joinpath(self.user.name)

        self.log.info(f"Duplicating release repository {repo_path_release}")
        self.log.info(f"Temporary path used for copying: {tmp_path_base}")

        try:
            self._run_command(f"git clone -b main '{repo_path_release}'", cwd=tmp_path_base)
            if checkout_main:
                self._run_command(f"git clone '{repo_path_user}'", cwd=tmp_path_base)
                self._run_command("git checkout -b main", cwd=tmp_path_user)
            else:
                self._run_command(f"git clone -b main '{repo_path_user}'", cwd=tmp_path_base)

            msg = f"Copying repo from {tmp_path_release} to {tmp_path_user}"
            self.log.info(msg)
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            shutil.copytree(tmp_path_release, tmp_path_user, ignore=ignore, dirs_exist_ok=True)
            cmd = "sh -c 'git add -A"
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
            ret = subprocess.run(shlex.split(command), check=True, cwd=cwd, capture_output=True)
            if capture_output:
                return str(ret.stdout, "utf-8")
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
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
        )
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
            obj = obj.replace(tzinfo=datetime.timezone.utc)
            return str(obj)
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, Model):
            return cls._serialize(obj.to_dict())
        return None


def authenticated(
    method: Callable[..., Optional[Awaitable[None]]],
) -> Callable[..., Optional[Awaitable[None]]]:
    """Decorate methods with this to require that the user be logged in.

    If the user is not logged in `tornado.web.HTTPError`
    with code 403 will be raised.
    """

    @functools.wraps(method)
    def wrapper(self: GraderBaseHandler, *args, **kwargs) -> Optional[Awaitable[None]]:
        if not self.current_user:
            raise HTTPError(403)
        return method(self, *args, **kwargs)

    return wrapper


@register_handler(r"\/?", VersionSpecifier.NONE)
class VersionHandler(GraderBaseHandler):
    async def get(self):
        self.write(f"Version {__version__}")


@register_handler(r"\/?", VersionSpecifier.V1)
class VersionHandlerV1(GraderBaseHandler):
    async def get(self):
        self.write("Version 1.0")


class RequestHandlerConfig(SingletonConfigurable):
    """This class exists to not avoid all request handlers to inherit
    from traitlets.config.Configurable and making all requests super
    slow. If a request handler needs configurable values, they can be
    accessed from this object."""

    autograde_executor_class = Type(
        default_value=LocalAutogradeExecutor,
        # TODO: why does using
        # LocalAutogradeExecutor give
        # subclass error?
        klass=object,
        allow_none=False,
        config=True,
    )

    # Git server file policy defaults
    git_max_file_size_mb = Integer(80, allow_none=False, config=True)
    git_max_file_count = Integer(512, allow_none=False, config=True)
    # empty list allows everything
    git_allowed_file_extensions = ListTrait(
        TraitType(Unicode), default_value=[], allow_none=False, config=True
    )
