"""API Contract: ExternalBaseModel with Sync Methods Support

This file defines the public API contract for ExternalBaseModel after
implementing synchronous methods support. It serves as the reference
for implementation and testing.

Feature: 002-sync-methods-support
Date: 2025-12-23
"""

from typing import Any, Self, TypedDict
from uuid import UUID

from pydantic import BaseModel


class ExternalReference(TypedDict):
    """External reference format for stored models."""

    class_name: str
    id: str


class ExternalConfigDict(TypedDict, total=False):
    """Configuration dictionary for external storage models."""

    storage: str


class ExternalBaseModel(BaseModel):
    """Base class for Pydantic models with external storage.

    This class extends pydantic.BaseModel with external storage capabilities
    while preserving 100% compatibility with pydantic's standard API.

    Key Design Principles:
    1. Pydantic methods (model_dump, model_validate, etc.) work exactly as
       in pydantic.BaseModel - synchronously, returning model data
    2. Storage operations use dedicated methods (save_external, load_external)
       that are clearly distinct from pydantic's serialization

    Example:
        >>> class User(ExternalBaseModel):
        ...     name: str
        ...     email: str
        ...     model_config = ExternalConfigDict(storage="postgresql://localhost/db")
        >>>
        >>> user = User(name="Alice", email="alice@example.com")
        >>>
        >>> # Pydantic API - works synchronously
        >>> data = user.model_dump()  # {"name": "Alice", "email": "alice@example.com"}
        >>>
        >>> # Storage API - dedicated methods
        >>> ref = await user.save_external()  # {"class_name": "User", "id": "..."}
        >>> restored = await User.load_external(ref)
    """

    _external_id: UUID | None
    _storage_url: str | None

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Dump model to dictionary (standard pydantic behavior).

        Returns a dictionary of model field values. This is the standard
        pydantic behavior - NO storage interaction.

        Returns:
            dict: Model field values as dictionary

        Note:
            This method is NOT overridden - it inherits directly from
            pydantic.BaseModel and works synchronously.
        """
        ...

    def model_dump_json(self, **kwargs: Any) -> str:
        """Dump model to JSON string (standard pydantic behavior).

        Returns a JSON string of model field values. This is the standard
        pydantic behavior - NO storage interaction.

        Returns:
            str: Model field values as JSON string

        Note:
            This method is NOT overridden - it inherits directly from
            pydantic.BaseModel and works synchronously.
        """
        ...

    @classmethod
    def model_validate(cls, obj: Any, **kwargs: Any) -> Self:
        """Validate and create model instance (standard pydantic behavior).

        Creates a model instance from a dictionary or object. This is the
        standard pydantic behavior - NO storage interaction.

        Args:
            obj: Dictionary or object to validate

        Returns:
            Model instance

        Note:
            This method is NOT overridden - it inherits directly from
            pydantic.BaseModel and works synchronously.
        """
        ...

    @classmethod
    def model_validate_json(cls, json_data: str | bytes, **kwargs: Any) -> Self:
        """Validate JSON and create model instance (standard pydantic behavior).

        Creates a model instance from a JSON string. This is the standard
        pydantic behavior - NO storage interaction.

        Args:
            json_data: JSON string or bytes to validate

        Returns:
            Model instance

        Note:
            This method is NOT overridden - it inherits directly from
            pydantic.BaseModel and works synchronously.
        """
        ...

    async def save_external(self) -> ExternalReference:
        """Persist model to external storage (async).

        Saves the model data to the configured storage backend and returns
        an external reference that can be used to restore the model later.

        Returns:
            ExternalReference: {"class_name": "...", "id": "..."} for restoration

        Raises:
            StorageConnectionError: If connection to backend fails
            StorageValidationError: If storage URL not configured

        Example:
            >>> user = User(name="Alice", email="alice@example.com")
            >>> ref = await user.save_external()
            >>> print(ref)  # {"class_name": "User", "id": "550e8400-..."}
        """
        ...

    def save_external_sync(self) -> ExternalReference:
        """Persist model to external storage (sync wrapper).

        Synchronous wrapper for save_external(). Use this when calling
        from a non-async context.

        Returns:
            ExternalReference: {"class_name": "...", "id": "..."} for restoration

        Raises:
            RuntimeError: If called from within an async context
            StorageConnectionError: If connection to backend fails
            StorageValidationError: If storage URL not configured

        Example:
            >>> user = User(name="Alice", email="alice@example.com")
            >>> ref = user.save_external_sync()  # No await needed
        """
        ...

    @classmethod
    async def load_external(cls, reference: ExternalReference) -> Self:
        """Load model from external storage using reference (async).

        Restores a model instance from external storage using an external
        reference previously obtained from save_external().

        Args:
            reference: External reference dict with class_name and id

        Returns:
            Restored model instance with all field values

        Raises:
            RecordNotFoundError: If no record exists with given id
            StorageValidationError: If class_name doesn't match
            StorageConnectionError: If connection to backend fails

        Example:
            >>> ref = {"class_name": "User", "id": "550e8400-..."}
            >>> user = await User.load_external(ref)
            >>> print(user.name)  # "Alice"
        """
        ...

    @classmethod
    def load_external_sync(cls, reference: ExternalReference) -> Self:
        """Load model from external storage using reference (sync wrapper).

        Synchronous wrapper for load_external(). Use this when calling
        from a non-async context.

        Args:
            reference: External reference dict with class_name and id

        Returns:
            Restored model instance with all field values

        Raises:
            RuntimeError: If called from within an async context
            RecordNotFoundError: If no record exists with given id
            StorageValidationError: If class_name doesn't match
            StorageConnectionError: If connection to backend fails

        Example:
            >>> ref = {"class_name": "User", "id": "550e8400-..."}
            >>> user = User.load_external_sync(ref)  # No await needed
        """
        ...

    @staticmethod
    def is_external_reference(data: Any) -> bool:
        """Check if data is an external reference format.

        Utility method to detect if a dictionary is an external reference
        (has exactly "class_name" and "id" keys).

        Args:
            data: Any value to check

        Returns:
            True if data is external reference format, False otherwise

        Example:
            >>> ExternalBaseModel.is_external_reference({"class_name": "User", "id": "..."})
            True
            >>> ExternalBaseModel.is_external_reference({"name": "Alice"})
            False
        """
        ...
