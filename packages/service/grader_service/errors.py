"""Module defining custom error classes for the grader service."""

from tornado.web import HTTPError


class APIError(HTTPError):
    """Base class for API-related errors."""

    def __init__(self, status_code: int, message: str, **kwargs):
        super().__init__(status_code, **kwargs)
        self.message = message


class ServiceError(Exception):
    """Base class for all service-layer errors."""


class NotFoundError(ServiceError):
    """A requested resource does not exist."""


class ConflictError(ServiceError):
    """The request conflicts with the current state of the resource."""


class InvalidInputError(ServiceError):
    """The request payload is semantically invalid."""


class PermissionDeniedError(ServiceError):
    """The user is not allowed to perform this operation."""
