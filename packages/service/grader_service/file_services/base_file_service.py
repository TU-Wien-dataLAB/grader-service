from pathlib import Path

from traitlets import Instance, Unicode, Union
from traitlets.config import LoggingConfigurable

from grader_service.orm import Assignment, Lecture, Submission


class FileService(LoggingConfigurable):
    """Base class defining the interface for handling assignment and submission files.

    Note: It is a de facto abstract class, but it cannot inherit from `abc.ABC`
    and `LoggingConfigurable` at the same time because of metaclasses conflict.
    """

    # TODO: Maybe only allow Path?
    grader_service_dir = Union([Unicode(), Instance(Path)], allow_none=False).tag(config=True)

    def init_submission_files(self, assignment: Assignment, username: str, message: str) -> None:
        """Initialize a new user's submission from the assignment files."""
        # TODO: "message" is git-specific!
        raise NotImplementedError()

    def validate_submission_exists(
        self, submission_hash: str, assignment: Assignment, username: str
    ) -> None:
        """Validate that the submission identified by the `submission_hash` exists.

        Should raise `FileServiceError` if the submission does not exist.
        """
        raise NotImplementedError()

    def edit_submission(self, submission: Submission) -> None:
        """Create or overwrite (reset) the instructor's changes to submission files."""
        raise NotImplementedError()

    def delete_lecture_files(self, lecture: Lecture) -> None:
        """Delete all associated files when a lecture is hard-deleted."""
        raise NotImplementedError()

    def delete_assignment_files(self, assignment: Assignment, lecture: Lecture) -> None:
        """Delete all associated files when an assignment is hard-deleted."""
        raise NotImplementedError()

    def delete_submission_files(self, submission: Submission) -> None:
        """Delete all associated files when a submission is hard-deleted."""
        raise NotImplementedError()


class FileServiceError(Exception):
    """Raised when there is a problem with the file service or a file operation fails."""
