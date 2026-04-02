# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.
import enum
import subprocess
import zlib
from http import HTTPStatus
from pathlib import Path
from string import Template
from typing import List, Optional

from sqlalchemy.orm.exc import NoResultFound
from tornado.ioloop import IOLoop
from tornado.iostream import StreamClosedError
from tornado.process import Subprocess
from tornado.web import HTTPError, stream_request_body

from grader_service.errors import APIError
from grader_service.file_services.git_files_service import construct_git_dir
from grader_service.handlers.base_handler import GraderBaseHandler, RequestHandlerConfig
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Lecture, Role, Submission
from grader_service.orm.takepart import Scope
from grader_service.registry import VersionSpecifier, register_handler


class GitRpcCmd(enum.StrEnum):
    UPLOAD_PACK = "upload-pack"
    SEND_PACK = "send-pack"
    RECEIVE_PACK = "receive-pack"


class GitBaseHandler(GraderBaseHandler):
    # TODO: This handler requires file_service to be a git one.

    @property
    def gitbase(self) -> Path:
        return Path(self.application.grader_service_dir) / "git"

    async def data_received(self, chunk: bytes):
        self.log.debug(f"Writing chunk of size {len(chunk)} to git process stdin")
        return self.process.stdin.write(chunk)

    def write_error(self, status_code: int, **kwargs) -> None:
        self.clear()
        if status_code == HTTPStatus.UNAUTHORIZED:
            self.set_header("WWW-Authenticate", 'Basic realm="User Visible Realm"')
        self.set_status(status_code)

    def on_finish(self):
        if hasattr(
            self, "process"
        ):  # if we exit super prepare (authentication) process is not created
            if self.process.stdin is not None:
                self.process.stdin.close()
            if self.process.stdout is not None:
                self.process.stdout.close()
            if self.process.stderr is not None:
                self.process.stderr.close()
            IOLoop.current().spawn_callback(self._wait_and_log)

    async def _wait_and_log(self):
        try:
            await self.process.wait_for_exit()
        except subprocess.CalledProcessError as e:
            stderr = b""
            if self.process.stderr:
                try:
                    stderr = await self.process.stderr.read_until_close()
                except Exception:
                    pass
            self.log.error(
                "Git process failed (code=%s): %s", e.returncode, stderr.decode(errors="replace")
            )

    async def git_response(self):
        try:
            while data := await self.process.stdout.read_bytes(8192, partial=True):
                if not data:
                    break
                self.write(data)
                await self.flush()
        except StreamClosedError:
            pass
        except Exception as e:
            self.log.error(f"Error from git response {e}")
            raise APIError(HTTPStatus.INTERNAL_SERVER_ERROR, message=str(e))

    def _parse_request_path(self) -> tuple[str, str, str, None | list[str]]:
        # If request is sent using jupyterhub as a proxy, remove 'services/grader' path prefix
        path = self.request.path.strip("/").removeprefix("services/grader")
        pathlets = path.strip("/").split("/")

        # pathlets should look like this:
        #   pathlets = ['git', <lecture_code>, <assignment_id>, <repo_type>, ...]
        # Note: The remaining tail can be empty, a sub_id, a username, or something else,
        # depending on the repo type and action.
        if len(pathlets) < 4:
            raise ValueError("Invalid request path")

        # cut git prefix
        _git, lect_code, assign_id, repo_type, *pathlets_tail = pathlets
        return lect_code, assign_id, repo_type, pathlets_tail

    def _check_git_repo_permissions(
        self,
        rpc: GitRpcCmd,
        role: Role,
        repo_type: GitRepoType,
        submission: Submission | None,
        username: str | None,
    ):
        if role.role == Scope.student and not self.user.is_admin:
            # 1. no interaction with source, release, and edit repo for students
            # 2. no pull allowed for autograde for students
            if (repo_type in {GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.EDIT}) or (
                repo_type == GitRepoType.AUTOGRADE and rpc == GitRpcCmd.UPLOAD_PACK
            ):
                raise HTTPError(HTTPStatus.FORBIDDEN, "forbidden action")

            # 3. students should not be able to pull other submissions
            if (repo_type == GitRepoType.FEEDBACK) and (rpc == GitRpcCmd.UPLOAD_PACK):
                if submission is None or submission.user_id != self.user.id:
                    raise HTTPError(HTTPStatus.NOT_FOUND, "Submission not found")

            # 4. students should not be able to access other user's repositories
            if repo_type == GitRepoType.USER and username != self.user.name:
                raise HTTPError(
                    HTTPStatus.FORBIDDEN, "Students cannot access other users' repositories"
                )

        # 5. no push allowed for autograde and feedback
        #    -> the autograder executor can push locally (will bypass this)
        if repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK} and rpc in [
            GitRpcCmd.SEND_PACK,
            GitRpcCmd.RECEIVE_PACK,
        ]:
            raise HTTPError(HTTPStatus.FORBIDDEN, "forbidden action for the repo type")

    def gitlookup(self, rpc: GitRpcCmd) -> Path | None:
        """Resolve and initialize a git repository path based on the request URL.

        Parses the request path to extract lecture, assignment, and repository type,
        validates permissions against the database, and returns the filesystem path
        to the appropriate git repository. Creates the directory and initializes
        the repository if they don't exist.

        Args:
            rpc: The Git RPC method name - used for permission checking.

        Returns:
            The absolute filesystem path to the git repository, or None if the request
            path is invalid or repository initialization fails.

        Raises:
            HTTPError: If the lecture, assignment, or user's role is not found;
                if the submission ID is invalid/missing; or if user's permissions
                for the git repository/action are insufficient.
        """
        try:
            # pathlets_tail can be empty, a sub_id, a username, or something else, depending
            # on the repo type and action.
            lect_code, assign_id, repo_type, pathlets_tail = self._parse_request_path()
        except ValueError:
            return None

        # Repo type "assignment" has been replaced by "user", so this should not happen,
        # but we are leaving this check for the time being, just to be on the safe side:
        if repo_type == "assignment":
            self.log.warning("Deprecated repo_type: 'assignment'! Setting it to 'user'")
            repo_type = GitRepoType.USER

        try:
            repo_type = GitRepoType(repo_type)
        except ValueError:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Invalid repo type")

        # get lecture, user's role in it, and assignment - if they exist
        try:
            lecture = self.session.query(Lecture).filter(Lecture.code == lect_code).one()
        except NoResultFound:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="Lecture was not found")

        role = self.get_role(lecture.id)

        try:
            assignment = self.get_assignment(lecture.id, int(assign_id))
        except ValueError:
            raise HTTPError(HTTPStatus.BAD_REQUEST, reason="Invalid assignment id")

        #  For the following repo types, sub_id is required and has to be a number
        submission = None
        sub_id = None
        if repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK, GitRepoType.EDIT}:
            try:
                sub_id = int(pathlets_tail[0])
            except (IndexError, TypeError, ValueError):
                raise HTTPError(HTTPStatus.BAD_REQUEST, "Invalid or missing submission id")
            submission = self.get_submission(lecture.id, assignment.id, int(sub_id))

        # if repo_type is user, get username from path, if given; otherwise take the logged-in user's name
        username = None
        if repo_type == GitRepoType.USER:
            if (
                pathlets_tail == ["info", "refs"]
                or pathlets_tail == [GitRpcCmd.UPLOAD_PACK]
                or pathlets_tail == [GitRpcCmd.RECEIVE_PACK]
            ):
                self.log.warning(
                    "DEPRECATED: No username specified in path, but info/refs "
                    "or git-upload-pack/git-receive-pack called. "
                    "Assuming user is trying to access their own repo."
                )
                username = self.user.name
            else:
                try:
                    username = pathlets_tail[0]
                except IndexError:
                    username = self.user.name
        elif repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK}:
            username = submission.user.name

        self._check_git_repo_permissions(rpc, role, repo_type, submission, username)

        path = construct_git_dir(
            self.gitbase, repo_type, lect_code, assign_id, submission_id=sub_id, username=username
        )
        if path is None:
            return None

        is_git = self.is_base_git_dir(path)
        if not is_git:
            path.mkdir(parents=True, exist_ok=True)
            self.log.info("Running: git init --bare")
            try:
                subprocess.run(["git", "init", "--bare", path], check=True)
            except subprocess.CalledProcessError:
                return None

            if repo_type == GitRepoType.USER:
                repo_path_release = construct_git_dir(
                    self.gitbase, GitRepoType.RELEASE, lect_code, assign_id
                )
                if not repo_path_release.exists():
                    return None
                self.file_service.init_submission(
                    assignment=assignment, message="Initialize with Release", checkout_main=True
                )

        self.write_pre_receive_hook(path)
        return path

    @staticmethod
    def is_base_git_dir(path: Path) -> bool:
        try:
            out = subprocess.run(
                ["git", "rev-parse", "--is-bare-repository"], cwd=path, capture_output=True
            )
            is_git = (out.returncode == 0) and ("true" in out.stdout.decode("utf-8"))
        except FileNotFoundError:
            is_git = False
        return is_git

    def write_pre_receive_hook(self, path: Path):
        hook_dir = path / "hooks"
        hook_dir.mkdir(exist_ok=True)

        hook_file = hook_dir / "pre-receive"
        if not hook_file.exists():
            tpl = Template(self._read_hook_template())
            hook = tpl.safe_substitute(
                {
                    "tpl_max_file_size": self._get_hook_max_file_size(),
                    "tpl_file_extensions": self._get_hook_file_allow_pattern(),
                    "tpl_max_file_count": self._get_hook_max_file_count(),
                }
            )
            with hook_file.open("wt") as f:
                hook_file.chmod(0o755)
                f.write(hook)

    @staticmethod
    def _get_hook_file_allow_pattern(extensions: Optional[List[str]] = None) -> str:
        pattern = ""
        if extensions is None:
            req_handler_conf = RequestHandlerConfig.instance()
            extensions = req_handler_conf.git_allowed_file_extensions
        if len(extensions) > 0:
            allow_patterns = ["\\." + s.strip(".").replace(".", "\\.") for s in extensions]
            pattern = "|".join(allow_patterns)
        return pattern

    @staticmethod
    def _get_hook_max_file_size():
        return RequestHandlerConfig.instance().git_max_file_size_mb

    @staticmethod
    def _get_hook_max_file_count():
        return RequestHandlerConfig.instance().git_max_file_count

    @staticmethod
    def _read_hook_template() -> str:
        file_path = Path(__file__).parent / "hook_templates" / "pre-receive"
        with open(file_path, mode="rt") as f:
            return f.read()

    def get_gitdir(self, rpc: GitRpcCmd) -> Path:
        """Determine the git repository for this request and create it if it does not exist yet."""
        gitdir = self.gitlookup(rpc)
        if gitdir is None:
            raise HTTPError(HTTPStatus.NOT_FOUND, reason="unable to find repository")
        self.log.info("Accessing git at: %s", gitdir)

        return gitdir


@register_handler(path="/.*/git-(.*)", version_specifier=VersionSpecifier.NONE)
@stream_request_body
class RPCHandler(GitBaseHandler):
    """Request handler for RPC calls

    Use this handler to handle example.git/git-upload-pack
    and example.git/git-receive-pack URLs"""

    async def prepare(self):
        await super().prepare()
        # check if payload is gzipped
        self._gunzip = None
        encoding = self.request.headers.get("Content-Encoding", "")
        if encoding == "gzip":
            # 16 + MAX_WBITS enables gzip decoding
            self._gunzip = zlib.decompressobj(16 + zlib.MAX_WBITS)

        # now setup git process
        rpc = self.path_args[0]
        try:
            self.rpc = GitRpcCmd(rpc)
        except ValueError:
            raise HTTPError(HTTPStatus.BAD_REQUEST, "Invalid Git RPC command")
        self.gitdir = self.get_gitdir(rpc=self.rpc)
        self.cmd = ["git", self.rpc, "--stateless-rpc", self.gitdir]
        self.log.info(f"Running command: {' '.join(self.cmd)}")
        self.process = Subprocess(
            self.cmd, stdin=Subprocess.STREAM, stderr=Subprocess.STREAM, stdout=Subprocess.STREAM
        )

    async def data_received(self, chunk: bytes):
        if self._gunzip:
            try:
                chunk = self._gunzip.decompress(chunk)
            except zlib.error:
                raise HTTPError(HTTPStatus.BAD_REQUEST, "Invalid gzip stream")
        return self.process.stdin.write(chunk)

    def on_finish(self):
        if self._gunzip:
            try:
                tail = self._gunzip.flush()
                if tail:
                    self.process.stdin.write(tail)
            except Exception:
                pass
        super().on_finish()

    async def post(self, rpc: GitRpcCmd):
        self.set_header("Content-Type", f"application/x-git-{rpc}-result")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        await self.git_response()
        await self.finish()


@register_handler(path="/.*/info/refs", version_specifier=VersionSpecifier.NONE)
class InfoRefsHandler(GitBaseHandler):
    """Request handler for info/refs

    Use this handler to handle example.git/info/refs?service= URLs"""

    async def prepare(self):
        await super().prepare()
        if self.get_status() != 200:
            return
        rpc = self.get_argument("service").removeprefix("git-")
        try:
            self.rpc = GitRpcCmd(rpc)
        except ValueError:
            raise HTTPError(HTTPStatus.BAD_REQUEST, "Invalid Git RPC command")

        self.cmd = [
            "git",
            self.rpc,
            "--stateless-rpc",
            "--advertise-refs",
            self.get_gitdir(self.rpc),
        ]
        self.log.info(f"Running command: {' '.join(self.cmd)}")
        self.process = Subprocess(
            self.cmd, stdin=Subprocess.STREAM, stderr=Subprocess.STREAM, stdout=Subprocess.STREAM
        )

    async def get(self):
        self.set_header("Content-Type", f"application/x-git-{self.rpc}-advertisement")
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

        prelude = f"# service=git-{self.rpc}\n"
        pkt_len = len(prelude) + 4
        size = f"{pkt_len:04x}"

        self.write(size)
        self.write(prelude)
        self.write("0000")  # flush-pkt
        await self.flush()

        await self.git_response()
        await self.finish()
