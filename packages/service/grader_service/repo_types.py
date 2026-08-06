import enum


class GitRepoType(enum.StrEnum):
    """Allowed repository types.

    SOURCE: The source files created by the instructor.
    RELEASE: The "student" version of the source files.
    USER: A user's copy of the release files, which can be submitted.
    AUTOGRADE: Autograded submission files.
    EDIT: Copy of the submission files, created by the instructor for manual editing.
    FEEDBACK: Final feedback for a submission.
    """

    SOURCE = "source"
    RELEASE = "release"
    USER = "user"
    AUTOGRADE = "autograde"
    EDIT = "edit"
    FEEDBACK = "feedback"
