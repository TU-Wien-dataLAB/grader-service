"""Base Authenticator class and the default PAM Authenticator"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import inspect
import re
import shlex
import sys
import warnings
from functools import partial
from shutil import which
from subprocess import PIPE, STDOUT, Popen

from traitlets import Any, Bool, Dict, Integer, Set, Unicode, default, observe
from traitlets.config import LoggingConfigurable

from .login import LoginHandler
from grader_service.utils import maybe_future, url_path_join


class Authenticator(LoggingConfigurable):
    """Base class for implementing an authentication provider for JupyterHub"""

    db = Any()

    enable_auth_state = Bool(
        False,
        config=True,
        help="""Enable persisting auth_state (if available).

        auth_state will be encrypted and stored in the Hub's database.
        This can include things like authentication tokens, etc.
        to be passed to Spawners as environment variables.

        Encrypting auth_state requires the cryptography package.

        Additionally, the JUPYTERHUB_CRYPT_KEY environment variable must
        contain one (or more, separated by ;) 32B encryption keys.
        These can be either base64 or hex-encoded.

        If encryption is unavailable, auth_state cannot be persisted.

        New in JupyterHub 0.8
        """,
    )

    auth_refresh_age = Integer(
        300,
        config=True,
        help="""The max age (in seconds) of authentication info
        before forcing a refresh of user auth info.

        Refreshing auth info allows, e.g. requesting/re-validating auth tokens.

        See :meth:`.refresh_user` for what happens when user auth info is refreshed
        (nothing by default).
        """,
    )

    refresh_pre_spawn = Bool(
        False,
        config=True,
        help="""Force refresh of auth prior to spawn.

        This forces :meth:`.refresh_user` to be called prior to launching
        a server, to ensure that auth state is up-to-date.

        This can be important when e.g. auth tokens that may have expired
        are passed to the spawner via environment variables from auth_state.

        If refresh_user cannot refresh the user auth data,
        launch will fail until the user logs in again.
        """,
    )

    request_otp = Bool(
        False,
        config=True,
        help="""
        Prompt for OTP (One Time Password) in the login form.

        .. versionadded:: 5.0
        """,
    )

    custom_html = Unicode(
        help="""
        HTML form to be overridden by authenticators if they want a custom authentication form.

        Defaults to an empty string, which shows the default username/password form.
        """
    )

    def get_custom_html(self, base_url):
        """Get custom HTML for the authenticator.

        .. versionadded: 1.4
        """
        return self.custom_html

    login_service = Unicode(
        help="""
        Name of the login service that this authenticator is providing using to authenticate users.

        Example: GitHub, MediaWiki, Google, etc.

        Setting this value replaces the login form with a "Login with <login_service>" button.

        Any authenticator that redirects to an external service (e.g. using OAuth) should set this.
        """
    )

    username_pattern = Unicode(
        help="""
        Regular expression pattern that all valid usernames must match.

        If a username does not match the pattern specified here, authentication will not be attempted.

        If not set, allow any username.
        """
    ).tag(config=True)

    @observe('username_pattern')
    def _username_pattern_changed(self, change):
        if not change['new']:
            self.username_regex = None
        self.username_regex = re.compile(change['new'])

    username_regex = Any(
        help="""
        Compiled regex kept in sync with `username_pattern`
        """
    )

    def validate_username(self, username):
        """Validate a normalized username

        Return True if username is valid, False otherwise.
        """
        if '/' in username:
            # / is not allowed in usernames
            return False
        if not username:
            # empty usernames are not allowed
            return False
        if username != username.strip():
            # starting/ending with space is not allowed
            return False
        if not self.username_regex:
            return True
        return bool(self.username_regex.match(username))

    username_map = Dict(
        help="""Dictionary mapping authenticator usernames to JupyterHub users.

        Primarily used to normalize OAuth user names to local users.
        """
    ).tag(config=True)

    delete_invalid_users = Bool(
        False,
        config=True,
        help="""Delete any users from the database that do not pass validation

        When JupyterHub starts, `.add_user` will be called
        on each user in the database to verify that all users are still valid.

        If `delete_invalid_users` is True,
        any users that do not pass validation will be deleted from the database.
        Use this if users might be deleted from an external system,
        such as local user accounts.

        If False (default), invalid users remain in the Hub's database
        and a warning will be issued.
        This is the default to avoid data loss due to config changes.
        """,
    )

    post_auth_hook = Any(
        config=True,
        help="""
        An optional hook function that you can implement to do some
        bootstrapping work during authentication. For example, loading user account
        details from an external system.

        This function is called after the user has passed all authentication checks
        and is ready to successfully authenticate. This function must return the
        authentication dict reguardless of changes to it.

        This maybe a coroutine.

        .. versionadded: 1.0

        Example::

            import os, pwd
            def my_hook(authenticator, handler, authentication):
                user_data = pwd.getpwnam(authentication['name'])
                spawn_data = {
                    'pw_data': user_data
                    'gid_list': os.getgrouplist(authentication['name'], user_data.pw_gid)
                }

                if authentication['auth_state'] is None:
                    authentication['auth_state'] = {}
                authentication['auth_state']['spawn_data'] = spawn_data

                return authentication

            c.Authenticator.post_auth_hook = my_hook

        """,
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_deprecated_methods()

    def _init_deprecated_methods(self):
        # handles deprecated signature *and* name
        # with correct subclass override priority!
        for old_name, new_name in (
                ('check_whitelist', 'check_allowed'),
                ('check_blacklist', 'check_blocked_users'),
                ('check_group_whitelist', 'check_allowed_groups'),
        ):
            old_method = getattr(self, old_name, None)
            if old_method is None:
                # no such method (check_group_whitelist is optional)
                continue

            # allow old name to have higher priority
            # if and only if it's defined in a later subclass
            # than the new name
            for cls in self.__class__.mro():
                has_old_name = old_name in cls.__dict__
                has_new_name = new_name in cls.__dict__
                if has_new_name:
                    break
                if has_old_name and not has_new_name:
                    warnings.warn(
                        "{0}.{1} should be renamed to {0}.{2} for JupyterHub >= 1.2".format(
                            cls.__name__, old_name, new_name
                        ),
                        DeprecationWarning,
                    )

                    # use old name instead of new
                    # if old name is overridden in subclass
                    def _new_calls_old(old_name, *args, **kwargs):
                        return getattr(self, old_name)(*args, **kwargs)

                    setattr(self, new_name, partial(_new_calls_old, old_name))
                    break

            # deprecate pre-1.0 method signatures
            signature = inspect.signature(old_method)
            if 'authentication' not in signature.parameters and not any(
                    param.kind == inspect.Parameter.VAR_KEYWORD
                    for param in signature.parameters.values()
            ):
                # adapt to pre-1.0 signature for compatibility
                warnings.warn(
                    """
                    {0}.{1} does not support the authentication argument,
                    added in JupyterHub 1.0. and is renamed to {2} in JupyterHub 1.2.

                    It should have the signature:

                    def {2}(self, username, authentication=None):
                        ...

                    Adapting for compatibility.
                    """.format(
                        self.__class__.__name__, old_name, new_name
                    ),
                    DeprecationWarning,
                )

                def wrapped_method(
                        original_method, username, authentication=None,
                        **kwargs
                ):
                    return original_method(username, **kwargs)

                setattr(self, old_name, partial(wrapped_method, old_method))

    async def run_post_auth_hook(self, handler, authentication):
        """
        Run the post_auth_hook if defined

        .. versionadded: 1.0

        Args:
            handler (tornado.web.RequestHandler): the current request handler
            authentication (dict): User authentication data dictionary. Contains the
                username ('name'), admin status ('admin'), and auth state dictionary ('auth_state').
        Returns:
            Authentication (dict):
                The hook must always return the authentication dict
        """
        if self.post_auth_hook is not None:
            authentication = await maybe_future(
                self.post_auth_hook(self, handler, authentication)
            )
        return authentication

    def normalize_username(self, username):
        """Normalize the given username and return it

        Override in subclasses if usernames need different normalization rules.

        The default attempts to lowercase the username and apply `username_map` if it is
        set.
        """
        username = username.lower()
        username = self.username_map.get(username, username)
        return username

    def check_allowed(self, username, authentication=None):
        """Check if a username is allowed to authenticate based on configuration

        Return True if username is allowed, False otherwise.
        No allowed_users set means any username is allowed.

        Names are normalized *before* being checked against the allowed set.

        .. versionchanged:: 1.0
            Signature updated to accept authentication data and any future changes

        .. versionchanged:: 1.2
            Renamed check_whitelist to check_allowed
        """
        if not self.allowed_users:
            # No allowed set means any name is allowed
            return True
        return username in self.allowed_users

    async def get_authenticated_user(self, handler, data):
        """Authenticate the user who is attempting to log in

        Returns user dict if successful, None otherwise.

        This calls `authenticate`, which should be overridden in subclasses,
        normalizes the username if any normalization should be done,
        and then validates the name in the allowed set.

        This is the outer API for authenticating a user.
        Subclasses should not override this method.

        The various stages can be overridden separately:
         - `authenticate` turns formdata into a username
         - `normalize_username` normalizes the username
         - `check_allowed` checks against the allowed usernames
         - `check_blocked_users` check against the blocked usernames
         - `is_admin` check if a user is an admin

        .. versionchanged:: 0.8
            return dict instead of username
        """
        authenticated = await maybe_future(self.authenticate(handler, data))
        if authenticated is None:
            return
        if isinstance(authenticated, dict):
            if 'name' not in authenticated:
                raise ValueError("user missing a name: %r" % authenticated)
        else:
            authenticated = {'name': authenticated}
        authenticated.setdefault('auth_state', None)
        # Leave the default as None, but reevaluate later post-allowed-check
        authenticated.setdefault('admin', None)

        # normalize the username
        authenticated['name'] = username = self.normalize_username(
            authenticated['name']
        )
        if not self.validate_username(username):
            self.log.warning("Disallowing invalid username %r.", username)
            return

        authenticated = await self.run_post_auth_hook(handler,
                                                      authenticated)

        return authenticated


    async def refresh_user(self, user, handler=None):
        """Refresh auth data for a given user

        Allows refreshing or invalidating auth data.

        Only override if your authenticator needs
        to refresh its data about users once in a while.

        .. versionadded: 1.0

        Args:
            user (User): the user to refresh
            handler (tornado.web.RequestHandler or None): the current request handler
        Returns:
            auth_data (bool or dict):
                Return **True** if auth data for the user is up-to-date
                and no updates are required.

                Return **False** if the user's auth data has expired,
                and they should be required to login again.

                Return a **dict** of auth data if some values should be updated.
                This dict should have the same structure as that returned
                by :meth:`.authenticate()` when it returns a dict.
                Any fields present will refresh the value for the user.
                Any fields not present will be left unchanged.
                This can include updating `.admin` or `.auth_state` fields.
        """
        return True

    async def authenticate(self, handler, data):
        """Authenticate a user with login form data

        This must be a coroutine.

        It must return the username on successful authentication,
        and return None on failed authentication.

        Checking allowed_users/blocked_users is handled separately by the caller.

        .. versionchanged:: 0.8
            Allow `authenticate` to return a dict containing auth_state.

        Args:
            handler (tornado.web.RequestHandler): the current request handler
            data (dict): The formdata of the login form.
                         The default form has 'username' and 'password' fields.
        Returns:
            user (str or dict or None):
                The username of the authenticated user,
                or None if Authentication failed.

                The Authenticator may return a dict instead, which MUST have a
                key `name` holding the username, and MAY have additional keys:

                - `auth_state`, a dictionary of auth state that will be persisted;
                - `admin`, the admin setting value for the user
                - `groups`, the list of group names the user should be a member of,
                  if Authenticator.manage_groups is True.
        """

    def pre_spawn_start(self, user, spawner):
        """Hook called before spawning a user's server

        Can be used to do auth-related startup, e.g. opening PAM sessions.
        """

    def post_spawn_stop(self, user, spawner):
        """Hook called after stopping a user container

        Can be used to do auth-related cleanup, e.g. closing PAM sessions.
        """

    def add_user(self, user):
        """Hook called when a user is added to JupyterHub

        This is called:
         - When a user first authenticates
         - When the hub restarts, for all users.

        This method may be a coroutine.

        By default, this just adds the user to the allowed_users set.

        Subclasses may do more extensive things, such as adding actual unix users,
        but they should call super to ensure the allowed_users set is updated.

        Note that this should be idempotent, since it is called whenever the hub restarts
        for all users.

        Args:
            user (User): The User wrapper object
        """
        if not self.validate_username(user.name):
            raise ValueError("Invalid username: %s" % user.name)
        if self.allowed_users:
            self.allowed_users.add(user.name)

    def delete_user(self, user):
        """Hook called when a user is deleted

        Removes the user from the allowed_users set.
        Subclasses should call super to ensure the allowed_users set is updated.

        Args:
            user (User): The User wrapper object
        """
        self.allowed_users.discard(user.name)

    manage_groups = Bool(
        False,
        config=True,
        help="""Let authenticator manage user groups

        If True, Authenticator.authenticate and/or .refresh_user
        may return a list of group names in the 'groups' field,
        which will be assigned to the user.

        All group-assignment APIs are disabled if this is True.
        """,
    )

    auto_login = Bool(
        False,
        config=True,
        help="""Automatically begin the login process

        rather than starting with a "Login with..." link at `/hub/login`

        To work, `.login_url()` must give a URL other than the default `/hub/login`,
        such as an oauth handler or another automatic login handler,
        registered with `.get_handlers()`.

        .. versionadded:: 0.8
        """,
    )

    auto_login_oauth2_authorize = Bool(
        False,
        config=True,
        help="""
        Automatically begin login process for OAuth2 authorization requests

        When another application is using JupyterHub as OAuth2 provider, it
        sends users to `/hub/api/oauth2/authorize`. If the user isn't logged
        in already, and auto_login is not set, the user will be dumped on the
        hub's home page, without any context on what to do next.

        Setting this to true will automatically redirect users to login if
        they aren't logged in *only* on the `/hub/api/oauth2/authorize`
        endpoint.

        .. versionadded:: 1.5

        """,
    )

    def login_url(self, base_url):
        """Override this when registering a custom login handler

        Generally used by authenticators that do not use simple form-based authentication.

        The subclass overriding this is responsible for making sure there is a handler
        available to handle the URL returned from this method, using the `get_handlers`
        method.

        Args:
            base_url (str): the base URL of the Hub (e.g. /hub/)

        Returns:
            str: The login URL, e.g. '/hub/login'
        """
        return url_path_join(base_url, 'login')

    def logout_url(self, base_url):
        """Override when registering a custom logout handler

        The subclass overriding this is responsible for making sure there is a handler
        available to handle the URL returned from this method, using the `get_handlers`
        method.

        Args:
            base_url (str): the base URL of the Hub (e.g. /hub/)

        Returns:
            str: The logout URL, e.g. '/hub/logout'
        """
        return url_path_join(base_url, 'logout')

    def get_handlers(self, app):
        """Return any custom handlers the authenticator needs to register

        Used in conjugation with `login_url` and `logout_url`.

        Args:
            app (JupyterHub Application):
                the application object, in case it needs to be accessed for info.
        Returns:
            handlers (list):
                list of ``('/url', Handler)`` tuples passed to tornado.
                The Hub prefix is added to any URLs.
        """
        return [('/login', LoginHandler)]


def _deprecated_method(old_name, new_name, version):
    """Create a deprecated method wrapper for a deprecated method name"""

    def deprecated(self, *args, **kwargs):
        warnings.warn(
            (
                "{cls}.{old_name} is deprecated in JupyterHub {version}."
                " Please use {cls}.{new_name} instead."
            ).format(
                cls=self.__class__.__name__,
                old_name=old_name,
                new_name=new_name,
                version=version,
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        old_method = getattr(self, new_name)
        return old_method(*args, **kwargs)

    return deprecated


# deprecate white/blacklist method names
for _old_name, _new_name, _version in [
    ("check_whitelist", "check_allowed", "1.2"),
    ("check_blacklist", "check_blocked_users", "1.2"),
]:
    setattr(
        Authenticator,
        _old_name,
        _deprecated_method(_old_name, _new_name, _version),
    )


class LocalAuthenticator(Authenticator):
    """Base class for Authenticators that work with local Linux/UNIX users

    Checks for local users, and can attempt to create them if they exist.
    """

    create_system_users = Bool(
        False,
        help="""
        If set to True, will attempt to create local system users if they do not exist already.

        Supports Linux and BSD variants only.
        """,
    ).tag(config=True)

    @default('add_user_cmd')
    def _add_user_cmd_default(self):
        """Guess the most likely-to-work adduser command for each platform"""
        if sys.platform == 'darwin':
            raise ValueError("I don't know how to create users on OS X")
        elif which('pw'):
            # Probably BSD
            return ['pw', 'useradd', '-m', '-n']
        else:
            # This appears to be the Linux non-interactive adduser command:
            return ['adduser', '-q', '--gecos', '""', '--disabled-password']

    uids = Dict(
        help="""
        Dictionary of uids to use at user creation time.
        This helps ensure that users created from the database
        get the same uid each time they are created
        in temporary deployments or containers.
        """
    ).tag(config=True)

    group_whitelist = Set(
        help="""DEPRECATED: use allowed_groups""",
    ).tag(config=True)

    allowed_groups = Set(
        help="""
        Allow login from all users in these UNIX groups.

        If set, allowed username set is ignored.
        """
    ).tag(config=True)

    @observe('allowed_groups')
    def _allowed_groups_changed(self, change):
        """Log a warning if mutually exclusive user and group allowed sets are specified."""
        if self.allowed_users:
            self.log.warning(
                "Ignoring Authenticator.allowed_users set because Authenticator.allowed_groups supplied!"
            )

    def check_allowed(self, username, authentication=None):
        if self.allowed_groups:
            return self.check_allowed_groups(username, authentication)
        else:
            return super().check_allowed(username, authentication)

    def check_allowed_groups(self, username, authentication=None):
        """
        If allowed_groups is configured, check if authenticating user is part of group.
        """
        if not self.allowed_groups:
            return False
        for grnam in self.allowed_groups:
            try:
                group = self._getgrnam(grnam)
            except KeyError:
                self.log.error('No such group: [%s]' % grnam)
                continue
            if username in group.gr_mem:
                return True
        return False

    async def add_user(self, user):
        """Hook called whenever a new user is added

        If self.create_system_users, the user will attempt to be created if it doesn't exist.
        """
        user_exists = await maybe_future(self.system_user_exists(user))
        if not user_exists:
            if self.create_system_users:
                await maybe_future(self.add_system_user(user))
            else:
                raise KeyError(
                    "User {} does not exist on the system."
                    " Set LocalAuthenticator.create_system_users=True"
                    " to automatically create system users from jupyterhub users.".format(
                        user.name
                    )
                )

        await maybe_future(super().add_user(user))

    @staticmethod
    def _getgrnam(name):
        """Wrapper function to protect against `grp` not being available
        on Windows
        """
        import grp

        return grp.getgrnam(name)

    @staticmethod
    def _getpwnam(name):
        """Wrapper function to protect against `pwd` not being available
        on Windows
        """
        import pwd

        return pwd.getpwnam(name)

    @staticmethod
    def _getgrouplist(name, group):
        """Wrapper function to protect against `os._getgrouplist` not being available
        on Windows
        """
        import os

        return os.getgrouplist(name, group)

    def system_user_exists(self, user):
        """Check if the user exists on the system"""
        try:
            self._getpwnam(user.name)
        except KeyError:
            return False
        else:
            return True

    def add_system_user(self, user):
        """Create a new local UNIX user on the system.

        Tested to work on FreeBSD and Linux, at least.
        """
        name = user.name
        cmd = [arg.replace('USERNAME', name) for arg in self.add_user_cmd]
        try:
            uid = self.uids[name]
            cmd += ['--uid', '%d' % uid]
        except KeyError:
            self.log.debug("No UID for user %s" % name)
        cmd += [name]
        self.log.info("Creating user: %s", ' '.join(map(shlex.quote, cmd)))
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode:
            err = p.stdout.read().decode('utf8', 'replace')
            raise RuntimeError(f"Failed to create system user {name}: {err}")
