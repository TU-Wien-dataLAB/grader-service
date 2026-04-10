import abc

from grader_service.orm import Assignment, Lecture, Submission


class BaseFileService(abc.ABC):
    """Abstract class defining the interface for handling assignment and submission files."""

    @abc.abstractmethod
    def init_submission_files(self, assignment: Assignment, message: str) -> None:
        """Initialize a new user's submission from the assignment files."""
        # TODO: "message" is git-specific!
        raise NotImplementedError()

    @abc.abstractmethod
    def validate_submission_exists(
        self, submission_hash: str, assignment: Assignment, username: str
    ) -> None:
        """Validate that the submission identified by the `submission_hash` exists.

        Should raise `FileServiceError` if the submission does not exist.
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def edit_submission(self, submission: Submission) -> None:
        """Create or overwrite (reset) the instructor's changes to submission files."""
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_lecture_files(self, lecture: Lecture) -> None:
        """Delete all associated files when a lecture is hard-deleted."""
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_assignment_files(self, assignment: Assignment, lecture: Lecture) -> None:
        """Delete all associated files when an assignment is hard-deleted."""
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_submission_files(self, submission: Submission) -> None:
        """Delete all associated files when a submission is hard-deleted."""
        raise NotImplementedError()


class FileServiceError(Exception):
    """Raised when there is a problem with the file service or a file operation fails."""
