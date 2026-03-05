import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List

from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission, User


class AssignmentFileService:
    """Service for assignment-related file operations"""

    def __init__(self, grader_service_dir: Path, user: User, log: Any):
        self.grader_service_dir = grader_service_dir
        self.tmpbase = self.grader_service_dir / "tmp"  # TODO: duplicated from base handler
        self.gitbase = self.grader_service_dir / "git"  # TODO: duplicated from base handler
        self.user = user
        self.log = log

    # def reset(self, assignment: Assignment):
    #     """Reset assignment files to their original state"""
    #     user_tmp_path = self.tmpbase / assignment.lecture.code / assignment.name / self.user.name
    #     # TODO: why is it assignment.name and not assignment.id???
    #     #  This path doesn't seem to be used anywhere/
    #     self.log.debug("User temporary Git base dir: %s", user_tmp_path)
    #     # Recreate temporary base Git dir for the user:  # TODO: why? is it used??
    #     if os.path.exists(user_tmp_path):
    #         shutil.rmtree(user_tmp_path)
    #     os.makedirs(user_tmp_path, exist_ok=True)
    #
    #     self.init_user_repo_from_release(assignment=assignment, message="Reset Assignment")

    # TODO: isn't it more like *submission* file service? (recreates user repo)
    def init_user_repo_from_release(
        self, assignment: Assignment, message: str, checkout_main: bool = False
    ) -> None:
        """...TODO..."""
        # TODO: this is ~duplicated from base handler.
        # TODO: this could probably replace `gitlookup`, i.e. at least parts thereof.
        # TODO: validate tmp_path_base for weird lecture codes and usernames.
        # TODO: why is it `assignment.id` here, but `assignment.name` in `user_base_path`??
        tmp_path_base = Path(
            self.tmpbase, assignment.lecture.code, str(assignment.id), str(self.user.name)
        )

        # Recreate temporary base Git dir for the user:
        if os.path.exists(tmp_path_base):
            shutil.rmtree(tmp_path_base)
        os.makedirs(tmp_path_base, exist_ok=True)

        tmp_path_release = tmp_path_base.joinpath("release")
        tmp_path_user = tmp_path_base.joinpath(self.user.name)

        repo_path_release = self._construct_git_dir(
            GitRepoType.RELEASE, assignment.lecture, assignment
        )
        repo_path_user = self._construct_git_dir(GitRepoType.USER, assignment.lecture, assignment)

        self.log.info("Creating user repository from the release repo; %s", repo_path_release)
        self.log.debug("Temporary path used for copying: %s", tmp_path_base)

        try:
            self._run_command(["git", "clone", "-b", "main", repo_path_release], cwd=tmp_path_base)
            if checkout_main:
                self._run_command(["git", "clone", repo_path_user], cwd=tmp_path_base)
                self._run_command(["git", "checkout", "-b", "main"], cwd=tmp_path_user)
            else:
                self._run_command(["git", "clone", "-b", "main", repo_path_user], cwd=tmp_path_base)

            self.log.debug("Copying repo from %s to %s", tmp_path_release, tmp_path_user)
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            shutil.copytree(tmp_path_release, tmp_path_user, ignore=ignore, dirs_exist_ok=True)
            self._run_command(["git", "add", "-A"], tmp_path_user)
            self._run_command(["git", "commit", "--allow-empty", "-m", message], tmp_path_user)
            self._run_command(["git", "push", "-u", "origin", "main"], tmp_path_user)
        finally:
            shutil.rmtree(tmp_path_base)

    def _run_command(
        self, command: List[str], cwd: Path | None = None, capture_output: bool = False
    ) -> str | None:
        # TODO: this is duplicated from base handler.
        # TODO: figure out error handling
        self.log.info("Running: %r", command)
        try:
            ret = subprocess.run(command, check=True, cwd=cwd, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise
        except FileNotFoundError as e:
            self.log.error(e)
            raise
        if capture_output:
            return str(ret.stdout, "utf-8")
        return None

    def _construct_git_dir(
        self,
        repo_type: GitRepoType,
        lecture: Lecture,
        assignment: Assignment,
        submission: Submission | None = None,
        username: str | None = None,
    ) -> str | None:
        """Returns the path of the repository based on
        the inputs or None if the repo_type is not recognized.

        Raises ValueError if the normalised path does not start with
        `self.gitbase`, to make it robust against fabricated lecture codes
        or usernames containing substrings like "../..".
        """
        # TODO: this is duplicated from base handler. Extract it somewhere? and refactor.
        # TODO: Maybe permissions check should be performed somewhere else. This shouldn't
        #  have to touch the database. I guess?
        assignment_path = os.path.abspath(
            os.path.join(self.gitbase, lecture.code, str(assignment.id))
        )
        allowed_types = {GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.EDIT}
        if repo_type in allowed_types:
            path = os.path.join(assignment_path, repo_type)
            if repo_type == GitRepoType.EDIT:
                path = os.path.join(path, str(submission.id))
        elif repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK}:
            type_path = os.path.join(assignment_path, repo_type, "user")
            if repo_type == GitRepoType.AUTOGRADE:
                assert submission is not None, f"Missing submission for repo type {repo_type}"
                path = os.path.join(type_path, submission.user.name)
            else:
                path = os.path.join(type_path, self.user.name)
        elif repo_type == GitRepoType.USER:
            user_path = os.path.join(assignment_path, repo_type)
            # we allow two different paths for user repos:
            #  - if username is not specified, we assume the user is trying to access their
            #    own repo, so we use `self.user.name`.
            #  - if username is specified, [we should check if the user has permission to access
            #    other users' repos, and then] use the specified username.
            if username is None:
                path = os.path.join(user_path, self.user.name)
            else:
                path = os.path.join(user_path, username)
        else:
            raise ValueError(f"Unknown repo type: {repo_type}")

        path = os.path.normpath(path)
        if not path.startswith(str(self.gitbase)):  # TODO: use something from pathlib probably
            raise ValueError("Invalid repository path.")

        return path
