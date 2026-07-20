import asyncio
import shutil
import subprocess
from pathlib import Path

from traitlets import observe, Unicode

from grader_service.file_services.base_file_service import FileService, FileServiceError
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission


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
     or None if the repo_type is not recognised.

     Note: This method does not check permissions to access the given repo type
     or submission; it only constructs the directory path.

    Raises ValueError if the normalised path does not start with
    `gitbase`, to make it robust against fabricated lecture codes
    or usernames containing substrings like "../..".
    """
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


class GitFileService(FileService):
    """Service for submission-related file operations"""

    # TODO: Apparently, not used anywhere! But hard-coded in helm charts and git workflows
    # service_git_username = Unicode(
    #     "grader-service", allow_none=False, help="Git username used by the service for commits"
    # ).tag(config=True)
    #
    # service_git_email = Unicode(
    #     "", allow_none=False, help="Git email used by the service for commits"
    # ).tag(config=True)

    git_executable = Unicode("git", allow_none=False).tag(config=True)

    @observe("grader_service_dir")
    def _observe_service_dir(self, change):
        path = change["new"]
        self.gitbase = Path(path) / "git"
        self.tmpbase = Path(path) / "tmp"

    def __init__(self, grader_service_dir: Path | str, **kwargs):
        super().__init__(**kwargs)
        self.grader_service_dir: Path = Path(grader_service_dir)
        self.tmpbase: Path = self.grader_service_dir / "tmp"
        self.gitbase: Path = self.grader_service_dir / "git"

        self._check_environment()

    def _check_environment(self):
        if shutil.which(self.git_executable) is None:
            msg = (
                "No git executable found! Git is necessary to run Grader Service "
                "with GitFileService!"
            )
            raise RuntimeError(msg)

        if not self.gitbase.exists():
            self.gitbase.mkdir()

        # check if git is configured so that git commits don't fail
        if (
            subprocess.run(
                [self.git_executable, "config", "init.defaultBranch"],
                check=False,
                capture_output=True,
            )
            .stdout.decode()
            .strip()
            != "main"
        ):
            raise RuntimeError("Git default branch has to be set to 'main'!")
        if (
            subprocess.run(
                [self.git_executable, "config", "user.name"], check=False, capture_output=True
            )
            .stdout.decode()
            .strip()
            == ""
        ):
            raise RuntimeError("Git user.name has to be set!")
        if (
            subprocess.run(
                [self.git_executable, "config", "user.email"], check=False, capture_output=True
            )
            .stdout.decode()
            .strip()
            == ""
        ):
            raise RuntimeError("Git user.email has to be set!")

    def validate_submission_exists(
        self, submission_hash: str, assignment: Assignment, username: str
    ) -> None:
        """Checks that user repo exists and `main` branch contains the commit with `submission_hash`."""
        git_repo_path = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.USER,
            lect_code=assignment.lecture.code,
            assignment_id=assignment.id,
            username=username,
        )

        # If no submissions for the student exists, we cannot reference a non-existing
        # commit_hash.
        if not git_repo_path.exists():
            raise FileServiceError("User git repository not found")
        try:
            subprocess.run(
                [self.git_executable, "branch", "main", "--contains", submission_hash],
                cwd=git_repo_path,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            raise FileServiceError("Submission commit not found")

    def init_submission_files(self, assignment: Assignment, username: str, message: str) -> None:
        """Creates a new user repository from release files.

        This method can also be used to "reset" one's own repo. Note that it does
        *not* reset its git history, but rather overwrites the submission files
        and creates a new commit.
        Release repository, as well as the remote dir for the user repository,
        have to exist already.
        """

        tmp_path_base = self.tmpbase / assignment.lecture.code / str(assignment.id) / username
        validate_path_relative_to(tmp_path_base, self.tmpbase)

        # Recreate temporary base Git dir for the user:
        if tmp_path_base.exists():
            shutil.rmtree(tmp_path_base)
        tmp_path_base.mkdir(parents=True, exist_ok=True)

        tmp_path_release = tmp_path_base / "release"
        tmp_path_user = tmp_path_base / username
        validate_path_relative_to(tmp_path_user, tmp_path_base)

        remote_path_release = construct_git_dir(
            self.gitbase, GitRepoType.RELEASE, assignment.lecture.code, assignment.id
        )
        remote_path_user = construct_git_dir(
            self.gitbase,
            GitRepoType.USER,
            assignment.lecture.code,
            assignment.id,
            username=username,
        )

        self.log.info("Creating user repository from the release repo; %s", remote_path_release)
        self.log.debug("Temporary path used for copying: %s", tmp_path_base)

        try:
            self._run_git([self.git_executable, "clone", remote_path_release], cwd=tmp_path_base)
            self._run_git([self.git_executable, "clone", remote_path_user], cwd=tmp_path_base)
            # Ensure the user repo is on `main`
            self._run_git([self.git_executable, "checkout", "-B", "main"], cwd=tmp_path_user)

            self.log.debug("Copying repo from %s to %s", tmp_path_release, tmp_path_user)
            ignore = shutil.ignore_patterns(".git", "__pycache__")
            shutil.copytree(tmp_path_release, tmp_path_user, ignore=ignore, dirs_exist_ok=True)
            self._run_git([self.git_executable, "add", "-A"], cwd=tmp_path_user)
            self._run_git(
                [self.git_executable, "commit", "--allow-empty", "-m", message], cwd=tmp_path_user
            )
            self._run_git([self.git_executable, "push", "-u", "origin", "main"], cwd=tmp_path_user)
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

        await self._run_git_async(
            [self.git_executable, "init", "--bare", "--initial-branch=main"], edit_repo_path
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
        await self._run_git_async(
            [self.git_executable, "init", "--initial-branch=main"], tmp_input_path
        )

        # Pull user repository
        await self._run_git_async(
            [self.git_executable, "pull", str(submission_repo_path), "main"], tmp_input_path
        )
        self.log.debug("Successfully cloned repo")

        # Checkout to correct submission commit
        await self._run_git_async(
            [self.git_executable, "checkout", submission.commit_hash], tmp_input_path
        )
        self.log.debug(f"Now at commit {submission.commit_hash}")

        # Copy files to output directory
        shutil.copytree(tmp_input_path, tmp_output_path, ignore=shutil.ignore_patterns(".git"))

        # Init local repository
        await self._run_git_async(
            [self.git_executable, "init", "--initial-branch=main"], tmp_output_path
        )

        # Add edit remote
        await self._run_git_async(
            [self.git_executable, "remote", "add", "edit", str(edit_repo_path)], tmp_output_path
        )
        self.log.debug("Successfully added edit remote")

        # Switch to main
        await self._run_git_async([self.git_executable, "switch", "-c", "main"], tmp_output_path)
        self.log.debug("Successfully switched to branch main")

        # Add files to staging
        await self._run_git_async([self.git_executable, "add", "-A"], tmp_output_path)
        self.log.debug("Successfully added files to staging")

        # Commit Files
        await self._run_git_async(
            [self.git_executable, "commit", "-m", "Initial commit"], tmp_output_path
        )
        self.log.debug("Successfully commited files")

        # Push copied files
        await self._run_git_async([self.git_executable, "push", "edit", "main"], tmp_output_path)
        self.log.info("Successfully created a repository for edited submission.")

    def _run_git(self, command: list[str], cwd: Path) -> None:
        """
        Execute a git command as a subprocess.

        Note that the command must start with the `git_executable`.

        Args:
            command: The git command to execute, as a list of strings.
            cwd: The working directory the subprocess should run in.
        Raises:
            `subprocess.CalledProcessError`: if `subprocess.run` fails.
            Any other exception thrown while running the subprocess is logged and also re-raised.

        """
        # TODO: Figure out error handling.
        if command[0] != self.git_executable:
            raise ValueError(f"Not a git command: {command}")
        self.log.debug('Running "%s"', " ".join(map(str, command)))
        try:
            subprocess.run(command, cwd=cwd, check=True)
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise FileServiceError("Subprocess Error")
        except Exception as e:
            self.log.error(e)
            raise
        return None

    async def _run_git_async(self, command: list[str], cwd: Path) -> None:
        """Run a git command asynchronously in a subprocess.

        Note that the command must start with the `git_executable`.

        Args:
            command: The git command to execute, as a list of strings.
            cwd: The working directory the subprocess should run in
        Returns:
            The command's stdout as str.
        Raises:
            FileServiceError: if the subprocess running the git command failed.
        """
        if command[0] != self.git_executable:
            raise ValueError(f"Not a git command: {command}")
        self.log.debug("Running: %s", " ".join(map(str, command)))
        try:
            ret = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=cwd
            )
        except Exception as e:
            self.log.error(e)
            raise
        stdout, stderr = await ret.communicate()
        if ret.returncode != 0:
            self.log.error(stderr.decode())
            raise FileServiceError("Subprocess Error")

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
