from pathlib import Path
from typing import Any

from traitlets.config import LoggingConfigurable

from grader_service.file_services import GitFileService
from grader_service.repo_types import GitRepoType
from grader_service.orm import Submission


class GitSubmissionManager(LoggingConfigurable):
    """
    Handles git-related operations performed by autograder executors:
    pulling from an input repo, and committing and pushing to the output repo.
    """

    input_repo_type = GitRepoType.USER
    output_repo_type = GitRepoType.AUTOGRADE

    def __init__(self, submission: Submission, **kwargs: Any):
        super().__init__(**kwargs)
        from grader_service import GraderService

        self.file_service: GitFileService = GraderService.instance().file_service
        self.submission = submission

        if self.input_repo_type == GitRepoType.USER and self.submission.edited:
            # User's submission was edited by the instructor - repo type has to be adjusted
            self.input_repo_type = GitRepoType.EDIT

        self.input_branch = "main"
        self.output_branch = f"submission_{self.submission.commit_hash}"

    def retrieve_submission(self, input_path: Path) -> None:
        """Inits and pulls the submission repository into the input path.

        :param input_path: The directory where the input repo will be created.
        """
        self.file_service.fetch_files(input_path, self.input_repo_type, self.submission)

    def push_results(self, filenames: list[str], output_path: Path) -> None:
        """Creates the output repository, commits and pushes the changes."""
        self.file_service.push_files(filenames, output_path, self.output_repo_type, self.submission)
