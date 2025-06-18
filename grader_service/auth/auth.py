"""Base Authenticator class"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
import re

from traitlets import Any, Bool, Callable, Dict, Integer, Set, Unicode, Union, default, observe
from traitlets.config import LoggingConfigurable

from grader_service.utils import maybe_future, url_path_join

from .login import LoginHandler


class Authenticator(LoggingConfigurable):
    """Base class for implementing an authentication provider for Grader Service."""

    login_redirect_url = Union(
        [Unicode(), Callable()],
        default_value="/",
        allow_none=False,
        help="""
        The default URL to redirect users when they successfully logged in.

        By default, this will likely be the URL of the JupyterHub server.

        Can be a Unicode string (e.g. '/hub/home') or a callable based on the handler object:

        ::

            def login_redirect_url_fn(handler):
                user = handler.current_user
                if user and user.admin:
                    return '/hub/admin'
                return '/hub/home'

            c.Authenticator.login_redirect_url = login_redirect_url_fn
        """,
    ).tag(config=True)

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

    admin_users = Set(
        help="""
        .. warning::
            Admin users do currently not have any special privileges
            in the Grader Service, but this may change in the future.

        Set of users that will have admin rights on the Grader Service instance.
        Admin access should be treated the same way root access is.

        Defaults to an empty set, in which case no user has admin access.
        """
    ).tag(config=True)

    any_allow_config = Bool(
        False,
        help="""Is there any allow config?

        Deployments can set this explicitly to True to suppress
        the "No allow config found" warning.

        Will be True if any config tagged with `.tag(allow_config=True)`
        or starts with `allow` is truthy.

        """,
    ).tag(config=True)

    @default("any_allow_config")
    def _default_any_allowed(self):
        for trait_name, trait in self.traits(config=True).items():
            if trait.metadata.get("allow_config", False) or trait_name.startswith("allow"):
                # this is only used for a helpful warning, so not the biggest deal if it's imperfect
                if getattr(self, trait_name):
                    return True
        return False

    def check_allow_config(self):
        """Log a warning if no allow config can be found.

        Could get a false positive if _only_ unrecognized allow config is used.
        Authenticators can apply `.tag(allow_config=True)` to label this config
        to make sure it is found.

        Subclasses can override to perform additonal checks and warn about likely
        authenticator configuration problems.

        .. versionadded:: 5.0
        """
        if not self.any_allow_config:
            self.log.warning(
                "No allow config found, it's possible that nobody can login to your Hub!\n"
                "You can set `c.Authenticator.allow_all = True` to allow any user who can login to access the Hub,\n"
                "or e.g. `allowed_users` to a set of users who should have access.\n"
                "You may suppress this warning by setting c.Authenticator.any_allow_config = True."
            )

    allowed_users = Set(
        help="""
        Set of usernames that are allowed to log in.

        Use this to limit which authenticated users may login.
        Default behavior: only users in this set are allowed.

        If empty, does not perform any restriction,
        in which case any authenticated user is allowed.

        Authenticators may extend :meth:`.Authenticator.check_allowed` to combine `allowed_users` with other configuration
        to either expand or restrict access.

        """
    ).tag(config=True)

    allow_all = Bool(
        False,
        config=True,
        help="""
        Allow every user who can successfully authenticate to access JupyterHub.

        False by default, which means for most Authenticators,
        _some_ allow-related configuration is required to allow users to log in.

        Authenticator subclasses may override the default with e.g.::

            @default("allow_all")
            def _default_allow_all(self):
                # if _any_ auth config (depends on the Authenticator)
                if self.allowed_users or self.allowed_groups or self.allow_existing_users:
                    return False
                else:
                    return True
        """,
    ).tag(allow_config=True)

    allow_existing_users = Bool(
        # dynamic default computed from allowed_users
        config=True,
        help="""
        Allow existing users to login.

        Defaults to True if `allowed_users` is set for historical reasons, and
        False otherwise.

        With this enabled, all users present in the Grader Service database are allowed to login.
        This has the effect of any user who has _previously_ been allowed to login
        via any means will continue to be allowed until the user is deleted.
        """,
    ).tag(allow_config=True)

    @default("allow_existing_users")
    def _allow_existing_users_default(self):
        """
        Computes the default value of allow_existing_users based on if
        allowed_users to align with original behavior not introduce a breaking
        change.
        """
        if self.allowed_users:
            return True
        return False

    blocked_users = Set(
        help="""
        Set of usernames that are not allowed to log in.

        Use this with supported authenticators to restrict which users can not log in. This is an
        additional block list that further restricts users, beyond whatever restrictions the
        authenticator has in place.

        If empty, does not perform any additional restriction.
        """
    ).tag(config=True)

    otp_prompt = Any(
        "OTP:",
        help="""
        The prompt string for the extra OTP (One Time Password) field.
        """,
    ).tag(config=True)

    request_otp = Bool(
        False,
        config=True,
        help="""
        Prompt for OTP (One Time Password) in the login form.
        """,
    )

    @observe("allowed_users")
    def _check_allowed_users(self, change):
        short_names = [name for name in change["new"] if len(name) <= 1]
        if short_names:
            sorted_names = sorted(short_names)
            single = "".join(sorted_names)
            string_set_typo = "set('%s')" % single
            self.log.warning(
                "Allowed set contains single-character names: %s; did you mean set([%r]) instead of %s?",
                sorted_names[:8],
                single,
                string_set_typo,
            )

    custom_html = Unicode(
        help="""
        HTML form to be overridden by authenticators if they want a custom authentication form.

        Defaults to an empty string, which shows the default username/password form.
        """
    )

    def get_custom_html(self, base_url):
        """Get custom HTML for the authenticator."""
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

    @observe("username_pattern")
    def _username_pattern_changed(self, change):
        if not change["new"]:
            self.username_regex = None
        self.username_regex = re.compile(change["new"])

    username_regex = Any(
        help="""
        Compiled regex kept in sync with `username_pattern`
        """
    )

    def validate_username(self, username):
        """Validate a normalized username

        Return True if username is valid, False otherwise.
        """
        if "/" in username:
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
        A hook function that you can implement to do some
        bootstrapping work during authentication. For example, loading user account
        details from an external system.

        This function is called after the user has passed all authentication checks
        and is ready to successfully authenticate. This function must return the
        auth_model dict reguardless of changes to it.
        The hook is called with 3 positional arguments: `(authenticator, handler, auth_model)`.

        This may be a coroutine.

        Example::

            import os
            import pwd
            def my_hook(authenticator, handler, auth_model):
                user_data = pwd.getpwnam(auth_model['name'])
                spawn_data = {
                    'pw_data': user_data
                    'gid_list': os.getgrouplist(auth_model['name'], user_data.pw_gid)
                }

                if auth_model['auth_state'] is None:
                    auth_model['auth_state'] = {}
                auth_model['auth_state']['spawn_data'] = spawn_data

                return auth_model

            c.Authenticator.post_auth_hook = my_hook

        """,
    )

    async def run_post_auth_hook(self, handler, auth_model):
        """
        Run the post_auth_hook if defined

        Args:
            handler (tornado.web.RequestHandler): the current request handler
            auth_model (dict): User authentication data dictionary. Contains the
                username ('name'), admin status ('admin'), and auth state dictionary ('auth_state').
        Returns:
            auth_model (dict):
                The hook must always return the auth_model dict
        """
        if self.post_auth_hook is not None:
            auth_model = await maybe_future(self.post_auth_hook(self, handler, auth_model))
        return auth_model

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

        Args:
            username (str):
                The normalized username
            authentication (dict):
                The authentication model, as returned by `.authenticate()`.
        Returns:
            allowed (bool):
                Whether the user is allowed
        Raises:
            web.HTTPError(403):
                Raising HTTPErrors directly allows customizing the message shown to the user.
        """
        if self.allow_all:
            return True
        return username in self.allowed_users

    def check_blocked_users(self, username, authentication=None):
        """Check if a username is blocked to authenticate based on Authenticator.blocked_users configuration

        Return True if username is allowed, False otherwise.
        No block list means any username is allowed.

        Names are normalized *before* being checked against the block list.

        Args:
            username (str):
                The normalized username
            authentication (dict):
                The authentication model, as returned by `.authenticate()`.
        Returns:
            allowed (bool):
                Whether the user is allowed
        Raises:
            web.HTTPError(403, message):
                Raising HTTPErrors directly allows customizing the message shown to the user.
        """
        if not self.blocked_users:
            # No block list means any name is allowed
            return True
        return username not in self.blocked_users

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
         - `check_blocked_users` check against the blocked usernames
         - `allow_all` is checked
         - `check_allowed` checks against the allowed usernames
         - `is_admin` check if a user is an admin

        """
        authenticated = await maybe_future(self.authenticate(handler, data))
        if authenticated is None:
            return
        if isinstance(authenticated, dict):
            if "name" not in authenticated:
                raise ValueError("user missing a name: %r" % authenticated)
        else:
            authenticated = {"name": authenticated}
        authenticated.setdefault("auth_state", None)
        # Leave the default as None, but reevaluate later post-allowed-check
        authenticated.setdefault("admin", None)

        # normalize the username
        authenticated["name"] = username = self.normalize_username(authenticated["name"])
        if not self.validate_username(username):
            self.log.warning("Disallowing invalid username %r.", username)
            return

        blocked_pass = await maybe_future(self.check_blocked_users(username, authenticated))

        if not blocked_pass:
            self.log.warning("User %r blocked. Stop authentication", username)
            return

        allowed_pass = self.allow_all
        if not allowed_pass:
            allowed_pass = await maybe_future(self.check_allowed(username, authenticated))

        if allowed_pass:
            if authenticated["admin"] is None:
                authenticated["admin"] = await maybe_future(self.is_admin(handler, authenticated))

            authenticated = await self.run_post_auth_hook(handler, authenticated)

            return authenticated
        else:
            self.log.warning("User %r not allowed.", username)
            return

    async def refresh_user(self, user, handler=None):
        """Refresh auth data for a given user

        Allows refreshing or invalidating auth data.

        Only override if your authenticator needs
        to refresh its data about users once in a while.

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

    def is_admin(self, handler, authentication):
        """Authentication helper to determine a user's admin status.

        Args:
            handler (tornado.web.RequestHandler): the current request handler
            authentication: The authentication dict generated by `authenticate`.
        Returns:
            admin_status (Bool or None):
                The admin status of the user, or None if it could not be
                determined or should not change.
        """
        return True if authentication["name"] in self.admin_users else None

    async def authenticate(self, handler, data):
        """Authenticate a user with login form data

        This must be a coroutine.

        It must return the username on successful authentication,
        and return None on failed authentication.

        Subclasses can also raise a `web.HTTPError(403, message)`
        in order to halt the authentication process
        and customize the error message that will be shown to the user.
        This error may be raised anywhere in the authentication process
        (`authenticate`, `check_allowed`, `check_blocked_users`).

        Checking allowed_users/blocked_users is handled separately by the caller.

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
                  `groups` MUST always be present if manage_groups is enabled.
        Raises:
            web.HTTPError(403):
                Raising errors directly allows customizing the message shown to the user.
        """

    async def load_managed_roles(self):
        """Load roles managed by authenticator.

        Returns a list of predefined role dictionaries to load at startup,
        following the same format as `JupyterHub.load_roles`.

        """
        if not self.manage_roles:
            raise ValueError("Managed roles can only be loaded when `manage_roles` is True")
        if self.reset_managed_roles_on_startup:
            raise NotImplementedError(
                "When `reset_managed_roles_on_startup` is used, the `load_managed_roles()`"
                " method must have a non-default implementation, because using the default"
                " implementation would remove all managed roles and role assignments."
            )
        return []

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
         - When a user first authenticates, _after_ all allow and block checks have passed
         - When the hub restarts, for all users in the database (i.e. users previously allowed)
         - When a user is added to the database, either via configuration or REST API

        This method may be a coroutine.

        By default, this adds the user to the allowed_users set if
        allow_existing_users is true.

        Subclasses may do more extensive things, such as creating actual system users,
        but they should call super to ensure the allowed_users set is updated.

        Note that this should be idempotent, since it is called whenever the hub restarts
        for all users.

        Args:
            user (User): The User wrapper object
        """
        if not self.validate_username(user.name):
            raise ValueError("Invalid username: %s" % user.name)
        if self.allow_existing_users and not self.allow_all:
            self.allowed_users.add(user.name)

    def delete_user(self, user):
        """Hook called when a user is deleted

        Removes the user from the allowed_users set.
        Subclasses should call super to ensure the allowed_users set is updated.

        Args:
            user (User): The User wrapper object
        """
        self.allowed_users.discard(user.name)

    # TODO: remove manage_groups since we only have roles
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
    manage_roles = Bool(
        False,
        config=True,
        help="""Let authenticator manage roles

        If True, Authenticator.authenticate and/or .refresh_user
        may return a list of roles in the 'roles' field,
        which will be added to the database.

        When enabled, all role management will be handled by the
        authenticator.

        """,
    )
    reset_managed_roles_on_startup = Bool(
        False,
        config=True,
        help="""Reset managed roles to result of `load_managed_roles()` on startup.

        If True:
          - stale managed roles will be removed,
          - stale assignments to managed roles will be removed.

        Any role not present in `load_managed_roles()` will be considered 'stale'.

        The 'stale' status for role assignments is also determined from `load_managed_roles()` result:

        - user role assignments status will depend on whether the `users` key is defined or not:

          * if a list is defined under the `users` key and the user is not listed, then the user role assignment will be considered 'stale',
          * if the `users` key is not provided, the user role assignment will be preserved;
        - service and group role assignments will be considered 'stale':

          * if not included in the `services` and `groups` list,
          * if the `services` and `groups` keys are not provided.

        """,
    )
    auto_login = Bool(
        False,
        config=True,
        help="""Automatically begin the login process

        rather than starting with a "Login with...".

        To work, `.login_url()` must give a URL other than the default,
        such as an oauth handler or another automatic login handler,
        registered with `.get_handlers()`.

        """,
    )

    auto_login_oauth2_authorize = Bool(
        False,
        config=True,
        help="""
        Automatically begin login process for OAuth2 authorization requests

        When another application is using Grader Service as OAuth2 provider, it
        sends users to `services/grader/api/oauth2/authorize`. If the user isn't logged
        in already, and auto_login is not set, the user will be dumped on the
        hub's home page, without any context on what to do next.

        Setting this to true will automatically redirect users to login if
        they aren't logged in *only* on the `services/grader/api/oauth2/authorize`
        endpoint.

        """,
    )

    def login_url(self, base_url):
        """Override this when registering a custom login handler

        Generally used by authenticators that do not use simple form-based authentication.

        The subclass overriding this is responsible for making sure there is a handler
        available to handle the URL returned from this method, using the `get_handlers`
        method.

        Args:
            base_url (str): the base URL of the Grader Service (e.g. /services/grader)

        Returns:
            str: The login URL, e.g. '/services/grader/login'
        """
        return url_path_join(base_url, "login")

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
        return url_path_join(base_url, "logout")

    def get_handlers(self, base_url: str):
        """Return any custom handlers the authenticator needs to register

        Used in conjugation with `login_url` and `logout_url`.

        Args:
            base_url (str):
                the application object, in case it needs to be accessed for info.
        Returns:
            handlers (list):
                list of ``('/url', Handler)`` tuples passed to tornado.
                The Hub prefix is added to any URLs.
        """
        return [(self.login_url(base_url), LoginHandler)]
