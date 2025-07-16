from traitlets import Unicode, default

from grader_service.auth.auth import Authenticator
from grader_service.auth.login import LogoutHandler


class DummyAuthenticator(Authenticator):
    """Dummy Authenticator for testing

    By default, any username + password is allowed
    If a non-empty password is set, any username will be allowed
    if it logs in with that password.

    """

    logout_handler = LogoutHandler

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
            if data["password"] == self.password:
                return data["username"]
            return None
        return data["username"]

    def get_handlers(self, base_url_path: str):
        base_handlers = super().get_handlers(base_url_path)
        dummy_handlers = [(self.logout_url(base_url_path), self.logout_handler)]
        return base_handlers + dummy_handlers
