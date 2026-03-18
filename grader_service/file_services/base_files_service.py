import abc


class BaseFileService(abc.ABC):
    """Abstract class defining the interface for handling assignment and submission files."""

    ...


class FileServiceError(Exception):
    """Raised when there is a problem with the file service or a file operation fails."""
