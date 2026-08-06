import typing
from pathlib import Path

from traitlets import Instance, Integer, List, TraitType, Unicode, Union
from traitlets.config import LoggingConfigurable

from grader_service.orm import Assignment, Lecture, Submission

if typing.TYPE_CHECKING:
    from grader_service.handlers import GitRepoType


class FileService(LoggingConfigurable):
    """Base class defining the interface for handling assignment and submission files.

    Note: It is a de facto abstract class, but it cannot inherit from `abc.ABC`
    and `LoggingConfigurable` at the same time because of metaclasses conflict.
    """

    # TODO: Maybe only allow Path?
    grader_service_dir = Union([Unicode(), Instance(Path)], allow_none=False).tag(config=True)

    # Git server file policy defaults (used in pre-receive hooks)
    max_file_size_mb = Integer(80, allow_none=False).tag(config=True)
    max_file_count = Integer(512, allow_none=False).tag(config=True)
    # empty list allows everything
    allowed_file_extensions = List(TraitType(Unicode), default_value=[], allow_none=False).tag(
        config=True
    )

    def validate_submission_exists(
        self, submission_hash: str, assignment: Assignment, username: str
    ) -> None:
        """Validate that the submission identified by the `submission_hash` exists.

        Should raise `FileServiceError` if the submission does not exist.
        """
        raise NotImplementedError()

    def init_user_files(self, assignment: Assignment, username: str, comment: str) -> None:
        """Initialize a new user's submission from the assignment files."""
        raise NotImplementedError()

    def edit_submission(self, submission: Submission) -> None:
        """Create or overwrite (reset) the instructor's changes to submission files."""
        raise NotImplementedError()

    def fetch_files(self, dir: Path, repo_type: "GitRepoType", submission: Submission):
        """Fetch the files of the `repo_type` for the `submission` into the `dir`."""
        # TODO: rename `repo_type` and `GitRepoType` to something more generic
        raise NotImplementedError()

    def push_files(  # TODO: think of a better name?
        self,
        filenames: list[str],
        dir: str | Path,
        repo_type: "GitRepoType",
        submission: Submission,
    ) -> None:
        """Save new/updated files of the `repo_type` for the `submission`."""
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
