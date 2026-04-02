import asyncio
import shutil
import subprocess
from pathlib import Path
from typing import Any

from grader_service.file_services.base_files_service import BaseFileService, FileServiceError
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission, User


def validate_path_relative_to(path: Path, base: Path) -> None:
    """Validate that `path` is relative to `base` directory.

    Prevents using fabricated variables (e.g. lecture codes or usernames containing
    substrings like "../..") to access directories outside of `base`.

    Raises:
        ValueError: if the resolved path is not relative to `base`.
    """
    path_obj = Path(path).resolve()
    if not path_obj.is_relative_to(base):
        raise ValueError("Invalid path")


def construct_git_dir(
    gitbase: Path,
    repo_type: GitRepoType,
    lect_code: str,
    assignment_id: int | str,
    submission_id: int | str | None = None,
    username: str | None = None,
) -> Path | None:
    """Returns the path of the repository based on the inputs,
     or None if the repo_type is not recognized.

    Raises ValueError if the normalised path does not start with
    `gitbase`, to make it robust against fabricated lecture codes
    or usernames containing substrings like "../..".
    """
    # TODO: Permissions check should be performed somewhere else. This method shouldn't
    #  have to touch the database.
    repo_type_path = gitbase / lect_code / str(assignment_id) / repo_type
    if repo_type in {GitRepoType.SOURCE, GitRepoType.RELEASE, GitRepoType.EDIT}:
        if repo_type == GitRepoType.EDIT:
            assert submission_id is not None, f"Missing submission_id for repo type {repo_type}"
            path = repo_type_path / str(submission_id)
        else:
            path = repo_type_path
    else:
        assert username is not None, f"Missing username for repo type {repo_type}"
        if repo_type in {GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK}:
            # Note: username should be that of the submission's user!
            path = repo_type_path / "user" / username
        elif repo_type == GitRepoType.USER:
            # we allow two different paths for user repos:
            #  - the logged-in user is trying to access their own repo,
            #  - the tutor/instructor accesses the repo of the user with the specified username.
            path = repo_type_path / username
        else:
            raise ValueError(f"Unknown repo type: {repo_type}")

    validate_path_relative_to(path, gitbase)
    return path


class GitFileService(BaseFileService):
    """Service for submission-related file operations"""

    def __init__(self, grader_service_dir: Path, user: User, log: Any):
        self.grader_service_dir: Path = grader_service_dir
        self.tmpbase: Path = self.grader_service_dir / "tmp"
        self.gitbase: Path = self.grader_service_dir / "git"  # TODO: duplicated in Git base handler
        self.user: User = user
        self.log: Any = log

    def validate_commit_hash(self, commit_hash: str, assignment: Assignment):
        """Checks that the user repo exists and that `main` branch contains the commit with the `commit_hash`."""
        git_repo_path = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.USER,
            lect_code=assignment.lecture.code,
            assignment_id=assignment.id,
            username=self.user.name,
        )

        # If no submissions for the student exists, we cannot reference a non-existing
        # commit_hash.
        if not git_repo_path.exists():
            raise FileServiceError("User git repository not found")
        try:
            subprocess.run(
                ["git", "branch", "main", "--contains", commit_hash],
                cwd=git_repo_path,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            raise FileServiceError("Commit not found")

    def create_submission_from_assignment_files(
        self, assignment: Assignment, message: str, checkout_main: bool = False
    ) -> None:
        """Creates a new user repository from release files.

        This method can also be used to reset (=recreate) a user repo.
        Release repository has to exist already.
        """

        tmp_path_base = self.tmpbase / assignment.lecture.code / str(assignment.id) / self.user.name
        validate_path_relative_to(tmp_path_base, self.tmpbase)

        # Recreate temporary base Git dir for the user:
        if tmp_path_base.exists():
            shutil.rmtree(tmp_path_base)
        tmp_path_base.mkdir(parents=True, exist_ok=True)

        tmp_path_release = tmp_path_base / "release"
        tmp_path_user = tmp_path_base / self.user.name

        repo_path_release = construct_git_dir(
            self.gitbase, GitRepoType.RELEASE, assignment.lecture.code, assignment.id
        )
        repo_path_user = construct_git_dir(
            self.gitbase,
            GitRepoType.USER,
            assignment.lecture.code,
            assignment.id,
            username=self.user.name,
        )

        self.log.info("Creating user repository from the release repo; %s", repo_path_release)
        self.log.debug("Temporary path used for copying: %s", tmp_path_base)

        try:
            self._run_command(["git", "clone", "-b", "main", repo_path_release], cwd=tmp_path_base)
            # TODO: Why are there these two cases? Do we need to keep them both?
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

    async def edit_submission(self, submission: Submission) -> None:
        """Creates or overwrites (resets) the repo which stores instructor's changes to submissions files."""
        assignment = submission.assignment
        lecture = assignment.lecture

        # Path to the (bare!) repository which will store edited submission files
        edit_repo_path = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.EDIT,
            lect_code=lecture.code,
            assignment_id=assignment.id,
            submission_id=submission.id,
        )
        # Path to repository of student which contains the submitted files
        submission_repo_path = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.USER,
            lect_code=lecture.code,
            assignment_id=assignment.id,
            username=submission.user.name,
        )
        if not submission_repo_path.exists():
            raise FileNotFoundError("The user submission repository does not exist")

        # (Re-)Creating bare repository
        if edit_repo_path.exists():
            shutil.rmtree(edit_repo_path)
        edit_repo_path.mkdir(parents=True, exist_ok=True)

        await self._run_command_async(
            ["git", "init", "--bare", "--initial-branch=main"], edit_repo_path
        )

        # Create temporary paths to copy the submission files in the edit repository
        tmp_path = self.tmpbase / lecture.code / str(assignment.id) / "edit" / str(submission.id)
        validate_path_relative_to(tmp_path, self.tmpbase)

        tmp_input_path = tmp_path / "input"
        tmp_output_path = tmp_path / "output"

        if tmp_path.exists():
            shutil.rmtree(tmp_path, ignore_errors=True)

        tmp_input_path.mkdir(parents=True, exist_ok=True)

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
        self, command: list[str], cwd: Path, capture_output: bool = False
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

    async def _run_command_async(self, command_args: list[str], cwd: Path):
        """Runs a command asynchronously in a subprocess.

        Args:
            command_args list[str]: List of command arguments to execute.
            cwd (Path): states where the command is getting run.

        Raises:
            FileServiceError: if the subprocess running the git command failed.
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

    def delete_lecture_files(self, lecture: Lecture) -> None:
        """Delete all associated directories of the lecture."""
        lecture_path = (self.gitbase / lecture.code).resolve()
        validate_path_relative_to(lecture_path, self.gitbase)
        tmp_lecture_path = (self.tmpbase / lecture.code).resolve()
        validate_path_relative_to(tmp_lecture_path, self.tmpbase)
        shutil.rmtree(lecture_path, ignore_errors=True)
        shutil.rmtree(tmp_lecture_path, ignore_errors=True)

    def delete_assignment_files(self, assignment: Assignment, lecture: Lecture) -> None:
        """Delete all associated directories of the assignment."""
        assignment_path = (self.gitbase / lecture.code / str(assignment.id)).resolve()
        validate_path_relative_to(assignment_path, self.gitbase)
        tmp_assignment_path = (self.tmpbase / lecture.code / str(assignment.id)).resolve()
        validate_path_relative_to(tmp_assignment_path, self.tmpbase)
        shutil.rmtree(assignment_path, ignore_errors=True)
        shutil.rmtree(tmp_assignment_path, ignore_errors=True)

    def delete_submission_files(self, submission: Submission) -> None:
        """Delete all associated directories of the submission."""
        lect_code = submission.assignment.lecture.code
        a_id = str(submission.assignment.id)

        assignment_path = (self.gitbase / lect_code / a_id).resolve()
        validate_path_relative_to(assignment_path, self.gitbase)
        tmp_assignment_path = (self.tmpbase / lect_code / a_id).resolve()
        validate_path_relative_to(tmp_assignment_path, self.tmpbase)

        target_names = {submission.user.name, str(submission.id)}
        for base_path in [assignment_path, tmp_assignment_path]:
            for dir_path in base_path.rglob("*"):
                if dir_path.is_dir() and dir_path.name in target_names:
                    shutil.rmtree(dir_path, ignore_errors=True)
