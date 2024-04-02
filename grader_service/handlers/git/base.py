import enum
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Optional

from sqlalchemy.exc import NoResultFound, MultipleResultsFound
from tornado import web
from tornado.web import HTTPError
from traitlets.config import SingletonConfigurable

from grader_service.handlers.base_handler import GraderBaseHandler
from grader_service.orm import Lecture, Assignment, Submission, Role, User
from grader_service.orm.takepart import Scope


class RepoType(enum.Enum):
    SOURCE = "source"
    RELEASE = "release"
    ASSIGNMENT = "assignment"  # replaced by USER_ASSIGNMENT or GROUP_ASSIGNMENT based on assignment type
    USER_ASSIGNMENT = "user"
    GROUP_ASSIGNMENT = "group"
    AUTOGRADE = "autograde"
    FEEDBACK = "feedback"
    EDIT = "edit"


class RPC(enum.Enum):
    UPLOAD_PACK = "upload-pack"
    SEND_PACK = "send-pack"
    RECEIVE_PACK = "receive-pack"


class GitBaseHandler(GraderBaseHandler):
    lecture: Lecture
    assignment: Assignment
    role: Role
    repo_type: RepoType
    submission: Optional[Submission] = None
    rpc: RPC

    async def prepare(self):
        await super().prepare()
        self.rpc = self.get_rpc()
        pathlets = self.request.path.strip("/").split("/")
        # pathlets = ['services', 'grader', 'git',
        #             'lecture_code', 'assignment_id', 'repo_type', ...]
        if len(pathlets) < 6:
            raise HTTPError(404)
        pathlets = pathlets[3:]

        try:
            self.lecture = (
                self.session.query(Lecture).filter(Lecture.code == pathlets[0]).one()  # noqa
            )
        except NoResultFound:
            raise HTTPError(404, reason="Lecture was not found")
        except MultipleResultsFound:
            raise HTTPError(500, reason="Found more than one lecture")
        self.role = self.session.query(Role).get((self.user.name, self.lecture.id))
        try:
            self.assignment = self.get_assignment(self.lecture.id, int(pathlets[1]))
        except ValueError:
            raise HTTPError(404, "Assignment not found")

        try:
            self.repo_type = RepoType(pathlets[2])
        except ValueError:
            raise HTTPError(400, "Invalid repo type")
        if self.repo_type == RepoType.ASSIGNMENT:
            self.repo_type = RepoType(self.assignment.type)

        if self.repo_type in [RepoType.AUTOGRADE, RepoType.FEEDBACK, RepoType.EDIT]:
            try:
                sub_id = int(pathlets[3])
            except (ValueError, IndexError):
                raise HTTPError(403)
            self.submission = self.session.query(Submission).get(sub_id)

        self.check_authorization()

        if not self.repo_exists():
            self.create_repo()

    def check_authorization(self):
        if self.role.role == Scope.student:
            # 1. no source or release interaction with source repo for students
            # 2. no pull allowed for autograde for students
            if ((self.repo_type in [RepoType.SOURCE, RepoType.RELEASE, RepoType.EDIT])
                    or (self.repo_type == RepoType.AUTOGRADE and self.rpc == RPC.UPLOAD_PACK)):
                raise HTTPError(403)

            # 3. students should not be able to pull other submissions
            #    -> add query param for sub_id
            if (self.repo_type == RepoType.FEEDBACK) and (self.rpc == RPC.UPLOAD_PACK):
                if self.submission is None or self.submission.username != self.user.name:
                    raise HTTPError(403)

        # 4. no push allowed for autograde and feedback
        #    -> the autograder executor can push locally (will bypass this)
        if ((self.repo_type in [RepoType.AUTOGRADE, RepoType.FEEDBACK])
                and (self.rpc in [RPC.SEND_PACK, RPC.RECEIVE_PACK])):
            raise HTTPError(403)

    def get_rpc(self) -> RPC:
        raise NotImplementedError

    def repo_exists(self) -> bool:
        raise NotImplementedError

    def create_repo(self):
        raise NotImplementedError

    @property
    def git_location(self) -> str:
        raise NotImplementedError


class RPCPathMixin(web.RequestHandler):
    def get_rpc(self) -> RPC:
        return RPC(self.path_args[0])


class InfoRefsPathMixin(web.RequestHandler):
    def get_rpc(self) -> RPC:
        return RPC(self.get_argument("service")[4:])


class GitServer(SingletonConfigurable):
    def __init__(self, grader_service_dir: str, **kwargs):
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir

    def register_handlers(self):
        raise NotImplementedError

    def git_location(self, repo_type: RepoType, user: User, assignment: Assignment,
                     submission: Optional[Submission] = None) -> str:
        # returns the path or URL of the git repository
        raise NotImplementedError

    def repo_exists(self, repo_type: RepoType, user: User, assignment: Assignment,
                    submission: Optional[Submission] = None) -> bool:
        raise NotImplementedError

    def create_repo(self, repo_type: RepoType, user: User, assignment: Assignment,
                    submission: Optional[Submission] = None) -> None:
        raise NotImplementedError

    def commit_hash_exists(self, commit_hash: str, repo_type: RepoType, user: User, assignment: Assignment,
                           submission: Optional[Submission] = None) -> bool:
        raise NotImplementedError

    def duplicate_release_repo(self, user: User, assignment: Assignment, message: str = "Reset Assignment",
                               checkout_main: bool = False):
        release_location = self.git_location(RepoType.RELEASE, user, assignment, None)
        user_location = self.git_location(RepoType(assignment.type), user, assignment, None)

        tmp_path_base = Path(
            self.grader_service_dir,
            "tmp",
            assignment.lecture.code,
            str(assignment.id),
            str(user.name)
        )

        # Deleting dir
        if os.path.exists(tmp_path_base):
            shutil.rmtree(tmp_path_base)

        os.makedirs(tmp_path_base, exist_ok=True)
        tmp_path_release = tmp_path_base.joinpath("release")
        tmp_path_user = tmp_path_base.joinpath(user.name)

        self.log.info(f"Duplicating release repository {release_location} to {user_location}")
        self.log.info(f"Temporary path used for copying: {tmp_path_base}")

        try:
            subprocess.run(shlex.split(f"git clone -b main '{release_location}'"), cwd=tmp_path_base)
            if checkout_main:
                subprocess.run(shlex.split(f"git clone '{user_location}'"), cwd=tmp_path_base)
                subprocess.run(shlex.split("git checkout -b main"), cwd=tmp_path_user)
            else:
                subprocess.run(shlex.split(f"git clone -b main '{user_location}'"), cwd=tmp_path_base)

            msg = f"Copying repo from {tmp_path_release} to {tmp_path_user}"
            self.log.info(msg)
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            shutil.copytree(tmp_path_release, tmp_path_user, ignore=ignore, dirs_exist_ok=True)

            cmd = f'sh -c \'git add -A && git commit --allow-empty -m "{message}"\''
            subprocess.run(shlex.split(cmd), cwd=tmp_path_user)
            subprocess.run(shlex.split("git push -u origin main"), cwd=tmp_path_user)
        finally:
            shutil.rmtree(tmp_path_base)
