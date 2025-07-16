import shlex
import sys
from shutil import which
from subprocess import PIPE, STDOUT, Popen

from traitlets import Bool, Dict, List, Set, default

from grader_service.auth.auth import Authenticator
from grader_service.utils import maybe_future


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

    add_user_cmd = List(
        help="""
        The command to use for creating users as a list of strings

        For each element in the list, the string USERNAME will be replaced with
        the user's username. The username will also be appended as the final argument.

        For Linux, the default value is:

            ['adduser', '-q', '--gecos', '""', '--disabled-password']

        To specify a custom home directory, set this to:

            ['adduser', '-q', '--gecos', '""', '--home', '/customhome/USERNAME', '--disabled-password']

        This will run the command:

            adduser -q --gecos "" --home /customhome/river --disabled-password river

        when the user 'river' is created.
        """
    ).tag(config=True)

    @default("add_user_cmd")
    def _add_user_cmd_default(self):
        """Guess the most likely-to-work adduser command for each platform"""
        if sys.platform == "darwin":
            raise ValueError("I don't know how to create users on macOS")
        elif which("pw"):
            # Probably BSD
            return ["pw", "useradd", "-m", "-n"]
        else:
            # This appears to be the Linux non-interactive adduser command:
            return ["adduser", "-q", "--gecos", '""', "--disabled-password"]

    uids = Dict(
        help="""
        Dictionary of uids to use at user creation time.
        This helps ensure that users created from the database
        get the same uid each time they are created
        in temporary deployments or containers.
        """
    ).tag(config=True)

    allowed_groups = Set(
        help="""
        Allow login from all users in these UNIX groups.
        """
    ).tag(config=True, allow_config=True)

    def check_allowed(self, username, authentication=None):
        if self.check_allowed_groups(username, authentication):
            return True
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
                self.log.error("No such group: [%s]" % grnam)
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
                    f"User {user.name} does not exist on the system."
                    " Set LocalAuthenticator.create_system_users=True"
                    " to automatically create system users from jupyterhub users."
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
        cmd = [arg.replace("USERNAME", name) for arg in self.add_user_cmd]
        try:
            uid = self.uids[name]
            cmd += ["--uid", "%d" % uid]
        except KeyError:
            self.log.debug("No UID for user %s" % name)
        cmd += [name]
        self.log.info("Creating user: %s", " ".join(map(shlex.quote, cmd)))
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT)
        p.wait()
        if p.returncode:
            err = p.stdout.read().decode("utf8", "replace")
            raise RuntimeError(f"Failed to create system user {name}: {err}")
