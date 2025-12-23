"""Custom exception hierarchy for external storage errors."""

from typing import Any
from uuid import UUID


class ExternalStorageError(Exception):
    """Base exception for all external storage errors."""

    pass


class StorageConnectionError(ExternalStorageError):
    """Raised when storage backend connection fails or is lost."""

    def __init__(self, message: str, url: str | None = None, cause: Exception | None = None):
        self.url = self._sanitize_url(url) if url else None
        self.cause = cause
        super().__init__(message)

    @staticmethod
    def _sanitize_url(url: str) -> str:
        """Remove credentials from URL for safe logging."""
        from urllib.parse import urlparse, urlunparse

        parsed = urlparse(url)
        if parsed.password:
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            if parsed.username:
                netloc = f"{parsed.username}:***@{netloc}"
            parsed = parsed._replace(netloc=netloc)
        return urlunparse(parsed)


class RecordNotFoundError(ExternalStorageError):
    """Raised when attempting to load a record that doesn't exist."""

    def __init__(self, id: UUID, class_name: str):
        self.id = id
        self.class_name = class_name
        super().__init__(
            f"Record not found: {class_name} with id={id}. "
            f"The record may have been deleted or never existed."
        )


class StorageValidationError(ExternalStorageError):
    """Raised when storage configuration or data validation fails."""

    def __init__(self, message: str, expected: Any = None, actual: Any = None):
        self.expected = expected
        self.actual = actual
        super().__init__(message)
