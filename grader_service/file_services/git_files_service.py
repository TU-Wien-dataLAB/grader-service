import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, List

from grader_service.file_services.base_files_service import BaseFileService, FileServiceError
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission, User


class BaseGitFileService(BaseFileService):
    def __init__(self, grader_service_dir: Path, user: User, log: Any):
        self.grader_service_dir: Path = grader_service_dir
        self.tmpbase: Path = self.grader_service_dir / "tmp"
        self.gitbase: Path = self.grader_service_dir / "git"  # TODO: duplicated from base handler
        self.user: User = user
        self.log: Any = log

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
        # TODO: this is duplicated from Git base handler. Extract it somewhere? and refactor.
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
                # TODO: This should only be available for admins/instructors/tutors
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
                # TODO: This should only be available for admins/instructors/tutors
                path = os.path.join(user_path, username)
        else:
            raise ValueError(f"Unknown repo type: {repo_type}")

        path = os.path.normpath(path)
        if not path.startswith(str(self.gitbase)):  # TODO: use something from pathlib probably
            raise ValueError("Invalid repository path.")

        return path


class SubmissionGitFileService(BaseGitFileService):
    """Service for submission-related file operations"""

    def validate_commit_hash(self, commit_hash: str, assignment: Assignment):
        """Checks that the user repo exists and that `main` branch contains the commit with the `commit_hash`."""
        git_repo_path = self._construct_git_dir(
            repo_type=GitRepoType.USER, lecture=assignment.lecture, assignment=assignment
        )

        # If no submissions for the student exists, we cannot reference a non-existing
        # commit_hash.
        if not os.path.exists(git_repo_path):
            raise FileServiceError("User git repository not found")
        try:
            subprocess.run(
                ["git", "branch", "main", "--contains", commit_hash],
                cwd=git_repo_path,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            raise FileServiceError("Commit not found")

    def create_submission(self): ...  # TODO?

    # TODO: Call this `create_submission`? (it recreates user repo; but is also used for resetting it)
    def init_user_repo_from_release(
        self, assignment: Assignment, message: str, checkout_main: bool = False
    ) -> None:
        """...TODO..."""

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

    async def edit_submission(self, submission: Submission):
        """Creates or overwrites (resets) the repository which stores changes of submissions files"""
        assignment = submission.assignment
        lecture = assignment.lecture

        # Path to the (bare!) repository which will store edited submission files
        edit_repo_path = self._construct_git_dir(
            repo_type=GitRepoType.EDIT,
            lecture=lecture,
            assignment=assignment,
            submission=submission,
        )
        # Path to repository of student which contains the submitted files
        submission_repo_path = self._construct_git_dir(
            repo_type=GitRepoType.USER,
            lecture=lecture,
            assignment=assignment,
            username=submission.user.name,
        )
        if not os.path.exists(submission_repo_path):
            raise FileNotFoundError("The user submission repository does not exist")

        # (Re-)Creating bare repository
        if os.path.exists(edit_repo_path):
            shutil.rmtree(edit_repo_path)
        os.makedirs(edit_repo_path, exist_ok=True)

        await self._run_command_async(
            ["git", "init", "--bare", "--initial-branch=main"], edit_repo_path
        )

        # Create temporary paths to copy the submission files in the edit repository
        tmp_path = self.tmpbase / lecture.code / str(assignment.id) / "edit" / str(submission.id)
        tmp_input_path = os.path.join(tmp_path, "input")
        tmp_output_path = os.path.join(tmp_path, "output")

        if os.path.exists(tmp_path):
            shutil.rmtree(tmp_path, ignore_errors=True)

        os.makedirs(tmp_input_path, exist_ok=True)

        # Init local repository
        await self._run_command_async(["git", "init", "--initial-branch=main"], tmp_input_path)

        # Pull user repository
        await self._run_command_async(
            ["git", "pull", str(submission_repo_path), "main"], tmp_input_path
        )
        self.log.debug("Successfully cloned repo")

        # Checkout to correct submission commit
        await self._run_command_async(["git", "checkout", submission.commit_hash], tmp_input_path)
        self.log.debug(f"Now at commit {submission.commit_hash}")

        # Copy files to output directory
        shutil.copytree(tmp_input_path, tmp_output_path, ignore=shutil.ignore_patterns(".git"))

        # Init local repository
        await self._run_command_async(["git", "init", "--initial-branch=main"], tmp_output_path)

        # Add edit remote
        await self._run_command_async(
            ["git", "remote", "add", "edit", str(edit_repo_path)], tmp_output_path
        )
        self.log.debug("Successfully added edit remote")

        # Switch to main
        await self._run_command_async(["git", "switch", "-c", "main"], tmp_output_path)
        self.log.debug("Successfully switched to branch main")

        # Add files to staging
        await self._run_command_async(["git", "add", "-A"], tmp_output_path)
        self.log.debug("Successfully added files to staging")

        # Commit Files
        await self._run_command_async(["git", "commit", "-m", "Initial commit"], tmp_output_path)
        self.log.debug("Successfully commited files")

        # Push copied files
        await self._run_command_async(["git", "push", "edit", "main"], tmp_output_path)
        self.log.info("Successfully created a repository for edited submission.")

    def _run_command(
        self, command: List[str], cwd: Path | None = None, capture_output: bool = False
    ) -> str | None:
        # TODO: There's also an async version, used for everything else.
        # TODO: Figure out error handling.
        # TODO: It only is used for running `git` commands, isn't it?
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

    async def _run_command_async(self, command_args: List[str], cwd: str | None = None):
        """Runs a command asynchronously in a subprocess.

        Args:
            command_args List[str]: List of command arguments to execute.
            cwd (str, optional): states where the command is getting run.
                                 Defaults to None.

        Raises:
            GitError: returns appropriate git error
        """
        # TODO: It only is used for running `git` commands, isn't it?
        self.log.debug("Running: %s", " ".join(command_args))
        ret = await asyncio.create_subprocess_exec(
            *command_args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
        )

        stdout, stderr = await ret.communicate()
        if ret.returncode != 0:
            self.log.error(stderr.decode())
            raise FileServiceError("Subprocess Error")
        return stdout.decode()

    def delete_lecture_files(self, lecture: Lecture):
        # delete all associated directories of the lecture
        lecture_path = os.path.abspath(os.path.join(self.gitbase, lecture.code))
        tmp_lecture_path = os.path.abspath(os.path.join(self.tmpbase, lecture.code))
        shutil.rmtree(lecture_path, ignore_errors=True)
        shutil.rmtree(tmp_lecture_path, ignore_errors=True)

    def delete_assignment_files(self, assignment: Assignment, lecture: Lecture):
        # delete all associated directories of the assignment
        assignment_path = os.path.abspath(
            os.path.join(self.gitbase, lecture.code, str(assignment.id))
        )
        tmp_assignment_path = os.path.abspath(
            os.path.join(self.tmpbase, lecture.code, str(assignment.id))
        )
        shutil.rmtree(assignment_path, ignore_errors=True)
        shutil.rmtree(tmp_assignment_path, ignore_errors=True)

    def delete_submission_files(self, submission: Submission):
        # delete all associated directories of the submission
        assignment_path = os.path.abspath(
            os.path.join(
                self.gitbase, submission.assignment.lecture.code, str(submission.assignment.id)
            )
        )
        tmp_assignment_path = os.path.abspath(
            os.path.join(
                self.tmpbase, submission.assignment.lecture.code, str(submission.assignment.id)
            )
        )
        target_names = {submission.user.name, str(submission.id)}
        matching_dirs = []
        for path in [assignment_path, tmp_assignment_path]:
            for root, dirs, _ in os.walk(path):
                for d in dirs:
                    if d in target_names:
                        matching_dirs.append(os.path.join(root, d))
        for path in matching_dirs:
            shutil.rmtree(path, ignore_errors=True)
