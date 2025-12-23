from typing import Any
from uuid import UUID


class ExternalStorageError(Exception):
    pass


class StorageConnectionError(ExternalStorageError):
    def __init__(self, message: str, url: str | None = None, cause: Exception | None = None):
        self.url = self._sanitize_url(url) if url else None
        self.cause = cause
        super().__init__(message)

    @staticmethod
    def _sanitize_url(url: str) -> str:
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
    def __init__(self, id: UUID, class_name: str):
        self.id = id
        self.class_name = class_name
        super().__init__(
            f"Record not found: {class_name} with id={id}. "
            f"The record may have been deleted or never existed."
        )


class StorageValidationError(ExternalStorageError):
    def __init__(self, message: str, expected: Any = None, actual: Any = None):
        self.expected = expected
        self.actual = actual
        super().__init__(message)
