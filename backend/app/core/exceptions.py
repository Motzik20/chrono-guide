"""Custom exceptions for the application."""


class NotFoundError(ValueError):
    """Raised when a requested resource is not found."""

    pass


class SystemError(RuntimeError):
    """Raised when a system-level error occurs."""

    pass
