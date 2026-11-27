"""All custom exceptions defined in one place."""


class ValidationError(Exception):
    """Base class for validation exceptions."""


class MissingRequiredArgumentError(ValidationError):
    """Exception raised for missing required request arguments."""


class IncorrectValueError(ValidationError):
    """Exception raised for incorrect values."""


class TokenError(ValidationError):
    """Exception raised for failed JWT decoding or verification."""


class InvalidAudienceError(ValidationError):
    """Exception raised for invalid audience."""


class LoginError(Exception):
    """Lookup of username in ID token failed"""
