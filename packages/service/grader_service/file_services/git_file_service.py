import asyncio
import shutil
import subprocess
from pathlib import Path

from traitlets import Unicode, observe, validate
from wrapt import async_to_sync

from grader_service.file_services.base_file_service import FileService, FileServiceError
from grader_service.repo_types import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission
from grader_service.orm.submission import AutoStatus, ManualStatus
from grader_service.utils import executable_validator


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
            if submission_id is None:
                raise ValueError(f"Missing submission_id for repo type {repo_type}")
            path = repo_type_path / str(submission_id)
        else:
            path = repo_type_path
    else:
        if username is None:
            raise ValueError(f"Missing username for repo type {repo_type}")
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

    @validate("git_executable")
    def _validate_executable(self, proposal):
        return executable_validator(proposal)

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
        if not self.gitbase.exists():
            self.gitbase.mkdir()

        # check if git is configured so that git commits don't fail
        default_branch = self._run_git(
            [self.git_executable, "config", "init.defaultBranch"], self.grader_service_dir
        ).strip()
        if default_branch != "main":
            raise RuntimeError("Git default branch has to be set to 'main'!")

        user_name = self._run_git(
            [self.git_executable, "config", "user.name"], self.grader_service_dir
        ).strip()
        if user_name == "":
            raise RuntimeError("Git user.name has to be set!")

        user_mail = self._run_git(
            [self.git_executable, "config", "user.email"], self.grader_service_dir
        ).strip()
        if user_mail == "":
            raise RuntimeError("Git user.email has to be set!")

    def _run_git(self, command: list[str], cwd: Path, may_fail: bool = False) -> str:
        """
        Execute a git command as a subprocess.

        Note that the command must start with the ``git_executable``.

        Args:
            command: The git command to execute, as a list of strings.
            cwd: The working directory the subprocess should run in.
            may_fail: Whether we expect that the command might fail (e.g. because
              we want to do something depending on its success/failure).
        Returns:
            The stdout of the process as text.
        Raises:
            ``FileServiceError`` if the command fails when it should not. This indicates
              an issue with the files or repositories - something that was not supposed
              to happen, and will be logged as an error.
            ``subprocess.CalledProcessError``: if ``may_fail=True`` and ``subprocess.run``
              fails; in other words, the command checks something, and this error just
              indicates one of the possible outcomes. It is not logged, and has to be
              handled by the caller.
            Any other exception thrown while running the subprocess is logged and also re-raised.

        """
        if command[0] != self.git_executable:
            raise ValueError(f"Not a git command: {command}")
        self.log.debug('Running "%s"', " ".join(map(str, command)))
        try:
            ret = subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            if may_fail:
                # This error is an expected possibility and will be handled. No need to log it.
                raise
            self.log.error(e.stderr)
            raise FileServiceError("Subprocess Error") from None
        except Exception as e:
            self.log.error(e)
            raise
        return ret.stdout

    async def _run_git_async(self, command: list[str], cwd: Path, may_fail: bool = False) -> str:
        """Run a git command asynchronously in a subprocess.

        Note that the command must start with the `git_executable`.

        Args:
            command: The git command to execute, as a list of strings.
            cwd: The working directory the subprocess should run in.
            may_fail: Whether we expect that the command might fail (e.g. because
              we want to do something depending on its success/failure).
        Returns:
            The stdout of the process as text.
        Raises:
            ``FileServiceError`` if the command fails when it should not. This indicates
              an issue with the files or repositories - something that was not supposed
              to happen, and will be logged as an error.
            ``subprocess.CalledProcessError``: if ``may_fail=True`` and ``subprocess.run``
              fails; in other words, the command checks something, and this error just
              indicates one of the possible outcomes. It is not logged, and has to be
              handled by the caller.
            Any other exception thrown while running the subprocess is logged and also re-raised.
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
            if may_fail:
                # This error is an expected possibility and will be handled. No need to log it.
                raise subprocess.CalledProcessError(ret.returncode, command, stdout, stderr)
            self.log.error(stderr.decode())
            raise FileServiceError("Subprocess Error")
        return stdout.decode("utf-8")

    async def is_bare_git_dir(self, path: Path) -> bool:
        """Check if the `path` is a directory with a bare git repo."""
        try:
            stdout = await self._run_git_async(
                [self.git_executable, "rev-parse", "--is-bare-repository"], cwd=path, may_fail=True
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            is_git = False
        else:
            is_git = "true" in stdout
        return is_git

    async def create_bare_repo(
        self, path: Path, recreate_dir: bool = False, initial_branch: str = "main"
    ) -> None:
        """Create and initialize a bare repo in the directory `path`.

        Args:
            path: the directory where the repo will be initialized
            recreate_dir: whether to remove and recreate the `path` dir first
            initial_branch: branch created on repo initialization
        """
        if recreate_dir and path.exists():
            self.log.info("Recreating the bare repo directory: %s", path)
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        self.log.debug("Running: git init --bare")
        await self._run_git_async(
            [self.git_executable, "init", "--bare", f"--initial-branch={initial_branch}"], cwd=path
        )

    async def validate_submission_exists(
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
            await self._run_git_async(
                [self.git_executable, "branch", "main", "--contains", submission_hash],
                cwd=git_repo_path,
                may_fail=True,
            )
        except subprocess.CalledProcessError:
            raise FileServiceError("Submission commit not found")

    def _prepare_tmp_dirs(
        self, base: Path, input_dir: str | Path = "input", output_dir: str | Path = "output"
    ) -> tuple[Path, Path]:
        """
        Recreate the base dir and create input and output subdirs in it.

        Base has to be relative to the ``self.tmpbase``.
        """
        validate_path_relative_to(base, self.tmpbase)
        if base.exists():
            shutil.rmtree(base)
        base.mkdir(parents=True)

        tmp_path_input = base / input_dir
        tmp_path_output = base / output_dir
        validate_path_relative_to(tmp_path_input, base)
        validate_path_relative_to(tmp_path_output, base)
        tmp_path_input.mkdir()
        tmp_path_output.mkdir()

        return tmp_path_input, tmp_path_output

    async def _copy_files_and_commit(
        self, input_path: Path, output_path: Path, message: str = "Initial commit"
    ) -> None:
        """Copy submission files from one repo to another, commit and push them."""
        self.log.debug("Copying submission files from %s to %s", input_path, output_path)
        ignore = shutil.ignore_patterns(".git", "__pycache__")
        shutil.copytree(input_path, output_path, ignore=ignore, dirs_exist_ok=True)

        await self._run_git_async([self.git_executable, "add", "-A"], cwd=output_path)
        await self._run_git_async(
            [self.git_executable, "commit", "--allow-empty", "-m", message], cwd=output_path
        )
        self.log.debug("Successfully commited files. Commit message: '%s'", message)
        await self._run_git_async(
            [self.git_executable, "push", "-u", "origin", "main"], cwd=output_path
        )
        self.log.debug("Successfully pushed the commit")

    async def init_user_files(self, assignment: Assignment, username: str, comment: str) -> None:
        """Copy submission files from release to user repo.

        This method can also be used to "reset" one's own repo. Note that it does
        *not* reset its git history, but rather overwrites the submission files
        and creates a new commit.

        Raises:
            FileNotFoundError if any of the release or user repositories do not exist.
        """
        l_code = assignment.lecture.code

        remote_path_release = construct_git_dir(
            self.gitbase, GitRepoType.RELEASE, l_code, assignment.id
        )
        if not remote_path_release.exists():
            raise FileNotFoundError("The release repository does not exist")
        remote_path_user = construct_git_dir(
            self.gitbase, GitRepoType.USER, l_code, assignment.id, username=username
        )
        if not remote_path_user.exists():
            raise FileNotFoundError("The user submission repository does not exist")

        tmp_base = self.tmpbase / l_code / str(assignment.id) / username
        tmp_path_input, tmp_path_output = self._prepare_tmp_dirs(
            tmp_base, "release", remote_path_user.name
        )

        self.log.info("Copying the release files from %s", remote_path_release)
        self.log.debug("Temporary path used for copying: %s", tmp_base)

        try:
            # Get the release files (no need to clone the whole repo)
            await self._run_git_async(
                [self.git_executable, "init", "--initial-branch=main"], cwd=tmp_path_input
            )
            await self._run_git_async(
                [self.git_executable, "pull", remote_path_release, "main"], cwd=tmp_path_input
            )

            # Clone the user repo (we need the whole clone, because we will be committing to it)
            await self._run_git_async(
                [self.git_executable, "clone", remote_path_user, tmp_path_output], cwd=tmp_base
            )
            # Ensure the user repo is on `main`
            await self._run_git_async(
                [self.git_executable, "checkout", "-B", "main"], cwd=tmp_path_output
            )

            # Copy files to the edit repo, commit and push the changes
            await self._copy_files_and_commit(tmp_path_input, tmp_path_output, comment)
            self.log.info("Successfully copied release files to user repository.")
        finally:
            shutil.rmtree(tmp_base)

    def fetch_files(self, dir: Path, repo_type: GitRepoType, submission: Submission):
        """Init and pull submission files from the repository of type ``repo_type`` into ``dir``.

        Note that this method does not clone the entire repository, but only pulls
        the specified branch into the ``dir``, so that the fetched files can be further
        processed (e.g. autograded, or copied over to initialize a different repo type).

        Args:
            dir: The directory where the input repo will be created; has to already exist.
            repo_type: Repo type from which the files are to be fetched
            submission: Submission whose files are to be fetched
        Raises:
            ValueError if repo_type is not one of the allowed values.
        """
        # TODO: does this logic belong here?
        if repo_type in [GitRepoType.USER, GitRepoType.EDIT]:
            input_branch = "main"
        elif repo_type == GitRepoType.AUTOGRADE:
            if (
                submission.auto_status in [AutoStatus.NOT_GRADED, AutoStatus.GRADING_FAILED]
                and submission.manual_status == ManualStatus.MANUALLY_GRADED
            ):
                # When submission hasn't been autograded or autograding failed,
                # pull from user repo to generate feedback
                repo_type = GitRepoType.USER
                input_branch = "main"
            else:
                input_branch = f"submission_{submission.commit_hash}"
        else:
            raise ValueError(f"Cannot fetch submission files with repo type {repo_type}")

        assignment: Assignment = submission.assignment
        l_code: str = assignment.lecture.code
        username: str = submission.user.name

        remote_repo_path = construct_git_dir(
            self.gitbase, repo_type, l_code, assignment.id, submission.id, username
        )

        self.log.info("Pulling repo %s into input directory", remote_repo_path)
        commands = [
            [self.git_executable, "init", "--initial-branch=main"],
            [self.git_executable, "pull", remote_repo_path, input_branch],
        ]
        # When autograding a user's submission, check out to the commit of submission
        if repo_type == GitRepoType.USER:
            commands.append([self.git_executable, "checkout", submission.commit_hash])

        for cmd in commands:
            self._run_git(cmd, dir)

        self.log.info("Successfully pulled files from the %s repo.", repo_type)

    # TODO: differences between `edit...` and `init_user_files`:
    #  - this re-creates the empty output bare repo, and `init_user...` only commits the changes
    #  - this checkouts the submission hash; `init_...` just checkouts main
    #  - edit one is async! (why only this one???) => some code has two variants, sync and async
    async def edit_submission(self, submission: Submission) -> None:
        """Create or overwrite (reset) the repo which stores instructor's changes to submissions files."""
        assignment = submission.assignment
        lecture = assignment.lecture

        # Create temporary paths to copy the submission files into the edit repository
        tmp_base = self.tmpbase / lecture.code / str(assignment.id) / "edit" / str(submission.id)
        tmp_path_input, tmp_path_output = self._prepare_tmp_dirs(tmp_base)

        # Path to repository of student which contains the submitted files
        remote_path_user = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.USER,
            lect_code=lecture.code,
            assignment_id=assignment.id,
            username=submission.user.name,
        )
        if not remote_path_user.exists():
            raise FileNotFoundError("The user submission repository does not exist")
        # Path to the repository which will store edited submission files (may not exist yet)
        remote_path_edit = construct_git_dir(
            gitbase=self.gitbase,
            repo_type=GitRepoType.EDIT,
            lect_code=lecture.code,
            assignment_id=assignment.id,
            submission_id=submission.id,
        )

        try:
            # Get user submission files (no need to clone the whole repo)
            self.fetch_files(tmp_path_input, GitRepoType.USER, submission)

            # (Re-)Create bare edit repository
            await self.create_bare_repo(remote_path_edit, recreate_dir=True)

            # Clone the (still empty) edit repository
            await self._run_git_async(
                [self.git_executable, "clone", remote_path_edit, tmp_path_output], tmp_path_output
            )
            await self._run_git_async(
                [self.git_executable, "checkout", "-B", "main"], tmp_path_output
            )
            self.log.debug("Successfully set up edit repo")

            # Copy files to the edit repo, commit and push the changes
            await self._copy_files_and_commit(tmp_path_input, tmp_path_output)
            self.log.info("Successfully created a repository for edited submission.")
        finally:
            shutil.rmtree(tmp_base)

    def push_files(
        self, filenames: list[str], dir: str | Path, repo_type: GitRepoType, submission: Submission
    ) -> None:
        """Create the repository of type `repo_type` at `dir`, commit and push the changes.

        This method is to be used on files produced by the autograder/feedback executor.
        When the submission if autograded/the feedback is generated for the first time,
        the bare repository is also initialized.

        Args:
            filenames: List of filenames in ``dir`` to commit
            dir: The directory where the input repo will be initialized. Should already
              exist and contain the ``filenames``
            repo_type: Repo type to which the files are to be pushed
            submission: Submission whose files are updated
        Raises:
            ValueError if repo_type is not one of the allowed values.
        """
        if repo_type == GitRepoType.AUTOGRADE:
            output_branch = f"submission_{submission.commit_hash}"
        elif repo_type == GitRepoType.FEEDBACK:
            output_branch = f"feedback_{submission.commit_hash}"
        else:
            raise ValueError(f"Invalid repo type {repo_type}")

        assignment: Assignment = submission.assignment
        l_code: str = assignment.lecture.code
        username: str = submission.user.name

        remote_repo_path = construct_git_dir(
            self.gitbase, repo_type, l_code, assignment.id, submission.id, username
        )
        if not remote_repo_path.exists():
            async_to_sync(self.create_bare_repo)(remote_repo_path)

        self._set_up_output_repo(Path(dir), output_branch)
        self._commit_files(filenames, Path(dir), msg=submission.commit_hash)

        self.log.info(f"Pushing to {remote_repo_path} at branch {output_branch}")
        self._run_git([self.git_executable, "push", "-uf", remote_repo_path, output_branch], dir)
        self.log.info("Pushing complete")

    def _set_up_output_repo(self, dir: Path, branch: str) -> None:
        """Initialize the repo at ``dir`` and switch to ``branch``."""
        if not dir.exists():
            self.log.debug("Creating directory %s", dir)
            dir.mkdir(parents=True)
        self.log.info("Initialising repo at %s", dir)
        self._run_git([self.git_executable, "init"], dir)
        self.log.debug("Switching to branch %r", branch)
        try:
            self._run_git([self.git_executable, "switch", branch], dir, may_fail=True)
        except subprocess.CalledProcessError:  # branch does not exist: create it
            self._run_git([self.git_executable, "switch", "-c", branch], dir)
            self.log.debug("Creating the new branch %r", branch)
        self.log.debug("Now at branch %r", branch)

    def _commit_files(self, filenames: list[str], dir: str | Path, msg: str) -> None:
        """
        Commit the provided files in the repo at `dir` with the provided commit message.
        """
        self.log.info(f"Committing files in {dir}")
        if not filenames:
            self.log.info("No files to commit.")
            return

        # Make sure we do not commit the gradebook.json
        filenames = [f for f in filenames if f != "gradebook.json"]

        self._run_git([self.git_executable, "add", "--", *filenames], dir)
        self._run_git([self.git_executable, "commit", "--allow-empty", "-m", msg], dir)

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
        l_code = submission.assignment.lecture.code
        a_id = str(submission.assignment.id)

        assignment_path = (self.gitbase / l_code / a_id).resolve()
        validate_path_relative_to(assignment_path, self.gitbase)
        tmp_assignment_path = (self.tmpbase / l_code / a_id).resolve()
        validate_path_relative_to(tmp_assignment_path, self.tmpbase)

        target_names = {submission.user.name, str(submission.id)}
        for base_path in [assignment_path, tmp_assignment_path]:
            for dir_path in base_path.rglob("*"):
                if dir_path.is_dir() and dir_path.name in target_names:
                    shutil.rmtree(dir_path, ignore_errors=True)
