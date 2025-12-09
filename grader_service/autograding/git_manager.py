import os
import subprocess
from typing import Any, List, Optional

from traitlets import Unicode, validate
from traitlets.config import LoggingConfigurable

from grader_service.autograding.utils import executable_validator
from grader_service.handlers.handler_utils import GitRepoType
from grader_service.orm import Assignment, Lecture, Submission


class GitSubmissionManager(LoggingConfigurable):
    """
    Handles git-related operations performed by autograder executors:
    pulling from an input repo, and committing and pushing to the output repo.
    """

    git_executable = Unicode("git", allow_none=False).tag(config=True)
    input_repo_type = GitRepoType.USER
    output_repo_type = GitRepoType.AUTOGRADE

    def __init__(self, grader_service_dir: str, submission: Submission, **kwargs: Any):
        super().__init__(**kwargs)
        self.grader_service_dir = grader_service_dir
        self.submission = submission

        if self.input_repo_type == GitRepoType.USER and self.submission.edited:
            # User's submission was edited by the instructor - repo type has to be adjusted
            self.input_repo_type = GitRepoType.EDIT

        self.input_branch = "main"
        self.output_branch = f"submission_{self.submission.commit_hash}"

    def _get_repo_path(self, repo_type: GitRepoType) -> str:
        """Determines the Git repository path for the submission."""
        assignment: Assignment = self.submission.assignment
        lecture: Lecture = assignment.lecture
        repo_name = self.submission.user.name

        base_repo_path = os.path.join(
            self.grader_service_dir, "git", lecture.code, str(assignment.id), repo_type
        )
        if repo_type in [GitRepoType.AUTOGRADE, GitRepoType.FEEDBACK]:
            path = os.path.join(base_repo_path, "user", repo_name)
        elif repo_type == GitRepoType.EDIT:
            path = os.path.join(base_repo_path, str(self.submission.id))
        elif repo_type == GitRepoType.USER:
            path = os.path.join(base_repo_path, repo_name)
        else:
            raise ValueError(f"Cannot determine repo path for repo type {repo_type}")

        path = os.path.normpath(path)

        if not path.startswith(self.grader_service_dir):
            self.log.error(
                f"Invalid repo path: {path}. Possibly suspicious values: "
                f"lecture code: '{lecture.code}' or user name: '{repo_name}'"
            )
            raise PermissionError("Invalid repository path.")

        return path

    def pull_submission(self, input_path: str) -> None:
        """Inits and pulls the submission repository into the input path.

        :param input_path: The directory where the input repo will be created.
        """
        input_repo_path = self._get_repo_path(self.input_repo_type)

        self.log.info(f"Pulling repo {input_repo_path} into input directory")
        commands = [
            [self.git_executable, "init"],
            [self.git_executable, "pull", input_repo_path, self.input_branch],
        ]

        # When autograding a user's submission, check out to the commit of submission
        if self.input_repo_type == GitRepoType.USER:
            commands.append([self.git_executable, "checkout", self.submission.commit_hash])

        for cmd in commands:
            self._run_git(cmd, input_path)

        self.log.info("Successfully cloned repo.")

    def _set_up_output_repo(self, output_path: str) -> None:
        """Initializes the output repo and switches to a separate branch named
        after the commit hash of the submission."""
        output_repo_path = self._get_repo_path(self.output_repo_type)

        if not os.path.exists(output_repo_path):
            os.makedirs(output_repo_path)
            self._run_git([self.git_executable, "init", "--bare", output_repo_path], output_path)

        self.log.info(f"Initialising repo at {output_path}")
        self._run_git([self.git_executable, "init"], output_path)
        self.log.info(f"Creating the new branch {self.output_branch} and switching to it")
        command = [self.git_executable, "switch", "-c", self.output_branch]
        self._run_git(command, output_path)
        self.log.info(f"Now at branch {self.output_branch}")

    def _commit_files(self, filenames: List[str], output_path: str) -> None:
        """
        Commits the provided files in the repo at `output_path`.
        """
        self.log.info(f"Committing files in {output_path}")

        if not filenames:
            self.log.info("No files to commit.")
            return

        # Make sure we do not commit the gradebook.json
        filenames = [f for f in filenames if f != "gradebook.json"]

        self._run_git([self.git_executable, "add", "--", *filenames], output_path)
        self._run_git(
            [self.git_executable, "commit", "-m", self.submission.commit_hash], output_path
        )

    def push_results(self, filenames: List[str], output_path: str) -> None:
        """Creates the output repository, commits and pushes the changes."""
        self._set_up_output_repo(output_path)
        self._commit_files(filenames, output_path)

        output_repo_path = self._get_repo_path(self.output_repo_type)

        self.log.info(f"Pushing to {output_repo_path} at branch {self.output_branch}")
        self._run_git(
            [self.git_executable, "push", "-uf", output_repo_path, self.output_branch], output_path
        )
        self.log.info("Pushing complete")

    def _run_git(self, command: list[str], cwd: Optional[str]) -> None:
        """
        Execute a git command as a subprocess.

        Args:
            command: The git command to execute, as a list of strings.
            cwd: The working directory the subprocess should run in.
        Raises:
            `subprocess.CalledProcessError`: if `subprocess.run` fails.
            Any other exception thrown while running the subprocess is logged and also re-raised.
        """
        assert command[0] == self.git_executable, f"Not a git command: {command}"
        self.log.debug('Running "%s"', " ".join(command))
        try:
            subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True,  # Decodes output to string
                check=True,  # Raises a CalledProcessError on non-zero exit code
            )
        except subprocess.CalledProcessError as e:
            self.log.error(e.stderr)
            raise
        except Exception as e:
            self.log.error(e)
            raise

    @validate("git_executable")
    def _validate_executable(self, proposal):
        return executable_validator(proposal)
