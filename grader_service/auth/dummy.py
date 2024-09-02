from traitlets import default, Unicode

from grader_service.auth.auth import Authenticator


class DummyAuthenticator(Authenticator):
    """Dummy Authenticator for testing

    By default, any username + password is allowed
    If a non-empty password is set, any username will be allowed
    if it logs in with that password.

    .. versionadded:: 1.0

    .. versionadded:: 5.0
        `allow_all` defaults to True,
        preserving default behavior.
    """

    @default("allow_all")
    def _allow_all_default(self):
        if self.allowed_users:
            return False
        else:
            # allow all by default
            return True

    password = Unicode(
        config=True,
        help="""
        Set a global password for all users wanting to log in.

        This allows users with any username to log in with the same static password.
        """,
    )

    def check_allow_config(self):
        super().check_allow_config()
        self.log.warning(
            f"Using testing authenticator {self.__class__.__name__}! This is not meant for production!"
        )

    async def authenticate(self, handler, data):
        """Checks against a global password if it's been set. If not, allow any user/pass combo"""
        if self.password:
            if data['password'] == self.password:
                return data['username']
            return None
        return data['username']