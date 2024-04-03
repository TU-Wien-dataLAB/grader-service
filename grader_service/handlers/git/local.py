import os
import shlex
import subprocess
from pathlib import Path
from string import Template
from typing import Optional, List

from tornado.ioloop import IOLoop
from tornado.process import Subprocess
from tornado.web import stream_request_body

from grader_service.handlers.base_handler import RequestHandlerConfig
from grader_service.handlers.git.base import GitBaseHandler, RPCPathMixin, InfoRefsPathMixin, RepoType, GitServer
from grader_service.orm import User, Lecture, Assignment, Submission
from grader_service.registry import HandlerPathRegistry


class GitLocalHandler(GitBaseHandler):
    cmd: str
    process: Subprocess

    async def data_received(self, chunk: bytes):
        return self.process.stdin.write(chunk)

    def write_error(self, status_code: int, **kwargs) -> None:
        self.clear()
        if status_code == 401:
            self.set_header("WWW-Authenticate",
                            'Basic realm="User Visible Realm"')
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
            IOLoop.current().spawn_callback(self.process.wait_for_exit)

    async def prepare(self):
        await super().prepare()
        self.write_pre_receive_hook()

    async def git_response(self):
        try:
            while data := await self.process.stdout.read_bytes(8192, partial=True):
                self.write(data)
                await self.flush()
        except Exception as e:
            print(f"Error from git response {e}")

    @property
    def git_location(self) -> str:
        return GitLocalServer.instance().git_location(self.repo_type, self.user, self.assignment, self.submission)

    def repo_exists(self) -> bool:
        return GitLocalServer.instance().repo_exists(self.repo_type, self.user, self.assignment, self.submission)

    def create_repo(self):
        GitLocalServer.instance().create_repo(self.repo_type, self.user, self.assignment, self.submission)

    def write_pre_receive_hook(self):
        hook_dir = os.path.join(self.git_location, "hooks")
        if not os.path.exists(hook_dir):
            os.mkdir(hook_dir)

        hook_file = os.path.join(hook_dir, "pre-receive")
        if not os.path.exists(hook_file):
            self.log.info(f"Writing pre-receive hook to {hook_file}")
            tpl = Template(self._read_hook_template())
            hook = tpl.safe_substitute({
                "tpl_max_file_size": self._get_hook_max_file_size(),
                "tpl_file_extensions": self._get_hook_file_allow_pattern(),
                "tpl_max_file_count": self._get_hook_max_file_count()
            })
            with open(hook_file, "wt") as f:
                os.chmod(hook_file, 0o755)
                f.write(hook)

    @staticmethod
    def _get_hook_file_allow_pattern(extensions: Optional[List[str]] = None) -> str:  # noqa E501
        pattern = ""
        if extensions is None:
            req_handler_conf = RequestHandlerConfig.instance()
            extensions = req_handler_conf.git_allowed_file_extensions
        if len(extensions) > 0:
            allow_patterns = ["\\." + s.strip(".").replace(".", "\\.") for s in extensions]  # noqa E501
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


# Actual implementations of handlers
@stream_request_body
class RPCLocalHandler(RPCPathMixin, GitLocalHandler):

    async def prepare(self):
        await super().prepare()
        self.cmd = f'git {self.rpc.value} --stateless-rpc "{self.git_location}"'
        self.log.info(f"Running command: {self.cmd}")
        self.process = Subprocess(
            shlex.split(self.cmd),
            stdin=Subprocess.STREAM,
            stderr=Subprocess.STREAM,
            stdout=Subprocess.STREAM,
        )

    async def post(self, rpc):
        self.set_header("Content-Type", "application/x-git-%s-result" % rpc)
        self.set_header(
            "Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"
        )
        await self.git_response()
        await self.finish()


class InfoRefsLocalHandler(InfoRefsPathMixin, GitLocalHandler):

    async def prepare(self):
        await super().prepare()
        self.cmd = f'git {self.rpc.value} --stateless-rpc --advertise-refs "{self.git_location}"'  # noqa E501
        self.log.info(f"Running command: {self.cmd}")
        self.process = Subprocess(
            shlex.split(self.cmd),
            stdin=Subprocess.STREAM,
            stderr=Subprocess.STREAM,
            stdout=Subprocess.STREAM,
        )

    async def get(self):
        self.set_header("Content-Type", "application/x-git-%s-advertisement" % self.rpc.value)
        self.set_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")

        prelude = f"# service=git-{self.rpc.value}\n0000"
        size = str(hex(len(prelude))[2:].rjust(4, "0"))
        self.write(size)
        self.write(prelude)
        await self.flush()

        await self.git_response()
        await self.finish()


class GitLocalServer(GitServer):
    def register_handlers(self):
        HandlerPathRegistry.add(RPCLocalHandler, path="/.*/git-(.*)")
        HandlerPathRegistry.add(InfoRefsLocalHandler, path="/.*/info/refs")

    @property
    def git_base_dir(self):
        return os.path.join(self.grader_service_dir, "git")

    def git_location(self, repo_type: RepoType, user: User, assignment: Assignment,
                     submission: Optional[Submission] = None) -> str:
        lecture = assignment.lecture
        assignment_path = os.path.abspath(
            os.path.join(self.git_base_dir, lecture.code, str(assignment.id))
        )
        if repo_type in [RepoType.SOURCE, RepoType.RELEASE, RepoType.EDIT]:
            path = os.path.join(assignment_path, repo_type.value)
            if repo_type == RepoType.EDIT:
                path = os.path.join(path, str(submission.id))
                self.log.info(path)
        elif repo_type in [RepoType.AUTOGRADE, RepoType.FEEDBACK]:
            type_path = os.path.join(assignment_path, repo_type.value, assignment.type)
            if assignment.type == "user":
                if repo_type == RepoType.AUTOGRADE:
                    path = os.path.join(type_path, submission.username)
                else:
                    path = os.path.join(type_path, user.name)
            else:
                raise NotImplementedError("group assignments not implemented")
        elif repo_type == RepoType.USER_ASSIGNMENT:
            user_path = os.path.join(assignment_path, repo_type.value)
            path = os.path.join(user_path, user.name)
        elif repo_type == RepoType.GROUP_ASSIGNMENT:
            raise NotImplementedError("group assignments not implemented")
        else:
            raise ValueError

        return path

    @staticmethod
    def is_base_git_dir(git_location: str):
        try:
            out = subprocess.run(["git", "rev-parse", "--is-bare-repository"], cwd=git_location, capture_output=True)
            is_git = out.returncode == 0 and "true" in out.stdout.decode("utf-8")
        except FileNotFoundError:
            is_git = False
        return is_git

    def repo_exists(self, repo_type: RepoType, user: User, assignment: Assignment,
                    submission: Optional[Submission] = None) -> bool:
        git_location = self.git_location(repo_type, user, assignment, submission)
        return os.path.exists(git_location) and self.is_base_git_dir(git_location)

    def create_repo(self, repo_type: RepoType, user: User, assignment: Assignment,
                    submission: Optional[Submission] = None) -> None:
        git_location = self.git_location(repo_type, user, assignment, submission)
        os.makedirs(git_location)
        # this path has to be a git dir -> call git init
        try:
            self.log.info("Running: git init --bare")
            subprocess.run(["git", "init", "--bare", git_location], check=True)
        except subprocess.CalledProcessError:
            return None

        if repo_type in [RepoType.USER_ASSIGNMENT, RepoType.GROUP_ASSIGNMENT]:
            GitLocalServer.instance().duplicate_release_repo(user, assignment, checkout_main=True)

    def commit_hash_exists(self, commit_hash: str, repo_type: RepoType, user: User, assignment: Assignment,
                           submission: Optional[Submission] = None) -> bool:
        if not self.repo_exists(repo_type, user, assignment, submission):
            return False

        git_repo_path = self.git_location(repo_type, user, assignment, submission)
        try:
            # Commit hash "0"*40 is used to differentiate between submissions created by instructors for students and normal submissions by any user.
            # In this case submissions for the student might not exist, so we cannot reference a non-existing commit_hash.
            # When submission is set to editted, autograder uses edit repository, so we don't need the commit_hash of the submission.
            if commit_hash != "0" * 40:
                subprocess.run(
                    ["git", "branch", "main", "--contains", commit_hash],
                    cwd=git_repo_path, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
