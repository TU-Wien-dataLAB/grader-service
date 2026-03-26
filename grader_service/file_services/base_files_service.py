import abc

from grader_service.orm import Assignment, Lecture, Submission


class BaseFileService(abc.ABC):
    """Abstract class defining the interface for handling assignment and submission files."""

    @abc.abstractmethod
    def create_submission_from_assignment_files(
        self, assignment: Assignment, message: str, checkout_main: bool = False
    ) -> None:
        # TODO: "message" and "checkout_main" are git-specific!
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
