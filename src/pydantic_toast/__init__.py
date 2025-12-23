"""pydantic-toast: External storage for Pydantic models."""

from pydantic_toast.base import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.exceptions import (
    ExternalStorageError,
    RecordNotFoundError,
    StorageConnectionError,
    StorageValidationError,
)
from pydantic_toast.registry import register_backend

__all__ = [
    "ExternalBaseModel",
    "ExternalConfigDict",
    "StorageBackend",
    "ExternalStorageError",
    "StorageConnectionError",
    "RecordNotFoundError",
    "StorageValidationError",
    "register_backend",
]

__version__ = "0.1.0"
