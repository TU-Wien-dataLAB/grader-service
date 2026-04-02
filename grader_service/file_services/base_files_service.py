import abc

from grader_service.orm import Assignment, Lecture, Submission


class BaseFileService(abc.ABC):
    """Abstract class defining the interface for handling assignment and submission files."""

    @abc.abstractmethod
    def init_submission(
        self, assignment: Assignment, message: str, checkout_main: bool = False
    ) -> None:
        """Initialize a new user's submission from the assignment files."""
        # TODO: "message" and "checkout_main" are git-specific!
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
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_lecture_files(self, lecture: Lecture) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_assignment_files(self, assignment: Assignment, lecture: Lecture) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def delete_submission_files(self, submission: Submission) -> None:
        raise NotImplementedError()


class FileServiceError(Exception):
    """Raised when there is a problem with the file service or a file operation fails."""
