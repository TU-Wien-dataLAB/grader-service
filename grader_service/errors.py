"""Module defining custom error classes for the grader service."""

from tornado.web import HTTPError


class APIError(HTTPError):
    """Base class for API-related errors."""

    def __init__(self, status_code: int, message: str, **kwargs):
        super().__init__(status_code, **kwargs)
        self.message = message
