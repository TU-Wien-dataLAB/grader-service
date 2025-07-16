from concurrent.futures import ThreadPoolExecutor

from tornado.concurrent import run_on_executor
from traitlets import Any, Bool, Set, Unicode, default

from grader_service.auth.local import LocalAuthenticator

try:
    import pamela
except Exception as e:
    pamela = None
    _pamela_error = e


class PAMAuthenticator(LocalAuthenticator):
    """Authenticate local UNIX users with PAM"""

    # run PAM in a thread, since it can be slow
    executor = Any()

    @default("executor")
    def _default_executor(self):
        return ThreadPoolExecutor(1)

    encoding = Unicode(
        "utf8",
        help="""
        The text encoding to use when communicating with PAM
        """,
    ).tag(config=True)

    service = Unicode(
        "login",
        help="""
        The name of the PAM service to use for authentication
        """,
    ).tag(config=True)

    open_sessions = Bool(
        False,
        help="""
        Whether to open a new PAM session when spawners are started.

        This may trigger things like mounting shared filesystems,
        loading credentials, etc. depending on system configuration.

        The lifecycle of PAM sessions is not correct,
        so many PAM session configurations will not work.

        If any errors are encountered when opening/closing PAM sessions,
        this is automatically set to False.

        .. versionchanged:: 2.2

            Due to longstanding problems in the session lifecycle,
            this is now disabled by default.
            You may opt-in to opening sessions by setting this to True.
        """,
    ).tag(config=True)

    check_account = Bool(
        True,
        help="""
        Whether to check the user's account status via PAM during authentication.

        The PAM account stack performs non-authentication based account
        management. It is typically used to restrict/permit access to a
        service and this step is needed to access the host's user access control.

        Disabling this can be dangerous as authenticated but unauthorized users may
        be granted access and, therefore, arbitrary execution on the system.
        """,
    ).tag(config=True)

    admin_groups = Set(
        help="""
        Authoritative list of user groups that determine admin access.
        Users not in these groups can still be granted admin status through admin_users.

        allowed/blocked rules still apply.

        Note: As of JupyterHub 2.0,
        full admin rights should not be required,
        and more precise permissions can be managed via roles.
        """
    ).tag(config=True)

    pam_normalize_username = Bool(
        False,
        help="""
        Round-trip the username via PAM lookups to make sure it is unique

        PAM can accept multiple usernames that map to the same user,
        for example DOMAIN\\username in some cases.  To prevent this,
        convert username into uid, then back to uid to normalize.
        """,
    ).tag(config=True)

    def __init__(self, **kwargs):
        if pamela is None:
            raise _pamela_error from None
        super().__init__(**kwargs)

    @run_on_executor
    def is_admin(self, handler, authentication):
        """PAM admin status checker. Returns Bool to indicate user admin status."""
        # Checks upper level function (admin_users)
        admin_status = super().is_admin(handler, authentication)
        username = authentication["name"]

        # If not yet listed as an admin, and admin_groups is on, use it authoritatively
        if not admin_status and self.admin_groups:
            try:
                # Most likely source of error here is a group name <-> gid mapping failure
                # This is most likely due to a typo in the configuration or in the case of LDAP/AD, a network
                # connectivity issue. Maybe a long one where the local caches have timed out, though PAM would
                # most likely would refuse to authenticate a remote user by that point.

                # It was decided that the best course of action on group resolution failure was to
                # fail to authenticate and raise instead of soft-failing and not changing admin status
                # (returning None instead of just the username) as this indicates some sort of system failure

                admin_group_gids = {self._getgrnam(x).gr_gid for x in self.admin_groups}
                user_group_gids = set(self._getgrouplist(username, self._getpwnam(username).pw_gid))
                admin_status = len(admin_group_gids & user_group_gids) != 0

            except Exception as e:
                if handler is not None:
                    self.log.error(
                        "PAM Admin Group Check failed (%s@%s): %s",
                        username,
                        handler.request.remote_ip,
                        e,
                    )
                else:
                    self.log.error("PAM Admin Group Check failed: %s", e)
                # re-raise to return a 500 to the user and indicate a problem. We failed, not them.
                raise

        return admin_status

    @run_on_executor
    def authenticate(self, handler, data):
        """Authenticate with PAM, and return the username if login is successful.

        Return None otherwise.
        """
        username = data["username"]
        password = data["password"]
        if "otp" in data:
            # OTP given, pass as tuple (requires pamela 1.1)
            password = (data["password"], data["otp"])
        try:
            pamela.authenticate(username, password, service=self.service, encoding=self.encoding)
        except pamela.PAMError as e:
            if handler is not None:
                self.log.warning(
                    "PAM Authentication failed (%s@%s): %s", username, handler.request.remote_ip, e
                )
            else:
                self.log.warning("PAM Authentication failed: %s", e)
            return None

        if self.check_account:
            try:
                pamela.check_account(username, service=self.service, encoding=self.encoding)
            except pamela.PAMError as e:
                if handler is not None:
                    self.log.warning(
                        "PAM Account Check failed (%s@%s): %s",
                        username,
                        handler.request.remote_ip,
                        e,
                    )
                else:
                    self.log.warning("PAM Account Check failed: %s", e)
                return None

        return username

    @run_on_executor
    def pre_spawn_start(self, user, spawner):
        """Open PAM session for user if so configured"""
        if not self.open_sessions:
            return
        try:
            pamela.open_session(user.name, service=self.service, encoding=self.encoding)
        except pamela.PAMError as e:
            self.log.warning("Failed to open PAM session for %s: %s", user.name, e)
            self.log.warning("Disabling PAM sessions from now on.")
            self.open_sessions = False

    @run_on_executor
    def post_spawn_stop(self, user, spawner):
        """Close PAM session for user if we were configured to opened one"""
        if not self.open_sessions:
            return
        try:
            pamela.close_session(user.name, service=self.service, encoding=self.encoding)
        except pamela.PAMError as e:
            self.log.warning("Failed to close PAM session for %s: %s", user.name, e)
            self.log.warning("Disabling PAM sessions from now on.")
            self.open_sessions = False

    def normalize_username(self, username):
        """Round-trip the username to normalize it with PAM

        PAM can accept multiple usernames as the same user, normalize them."""
        if self.pam_normalize_username:
            import pwd

            uid = pwd.getpwnam(username).pw_uid
            username = pwd.getpwuid(uid).pw_name
            username = self.username_map.get(username, username)
            return username
        else:
            return super().normalize_username(username)
