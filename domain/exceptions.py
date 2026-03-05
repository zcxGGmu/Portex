"""Domain exception definitions."""


class DomainError(Exception):
    """Base exception for domain-layer errors."""


class NotFoundError(DomainError):
    """Raised when a requested domain object does not exist."""
