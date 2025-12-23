"""API Contract: ExternalTypeAdapter

This module defines the public API contract for the ExternalTypeAdapter feature.
It serves as the specification for implementation - all public signatures,
types, and docstrings defined here must be implemented exactly.

Feature: 004-type-adapter
Date: 2025-12-23
"""

from datetime import UTC, datetime
from typing import Any, get_args, get_origin
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import TypeAdapter, ValidationError

from pydantic_toast.base import ExternalReference, _run_sync
from pydantic_toast.exceptions import RecordNotFoundError, StorageValidationError
from pydantic_toast.registry import get_global_registry


def _get_type_name(tp: type[Any]) -> str:
    """Generate a canonical string representation of a type.

    Args:
        tp: Any Python type (class, generic, etc.)

    Returns:
        String representation like "User", "list[User]", "dict[str, int]"

    Examples:
        >>> _get_type_name(int)
        'int'
        >>> _get_type_name(list[str])
        'list[str]'
        >>> _get_type_name(dict[str, int])
        'dict[str, int]'
    """
    origin = get_origin(tp)
    if origin is None:
        return getattr(tp, "__name__", str(tp))

    args = get_args(tp)
    if not args:
        return getattr(origin, "__name__", str(origin))

    arg_names = ", ".join(_get_type_name(arg) for arg in args)
    origin_name = getattr(origin, "__name__", str(origin))
    return f"{origin_name}[{arg_names}]"


class ExternalTypeAdapter[T]:
    """Adapter for storing arbitrary Python types in external storage.

    Wraps Pydantic's TypeAdapter to provide external storage capabilities
    for types that cannot inherit from ExternalBaseModel. Supports TypedDict,
    dataclasses, NamedTuple, collections, and any Pydantic-compatible type.

    Args:
        type_: The type to validate and store. Must be Pydantic-compatible.
        storage_url: Storage backend URL (e.g., "postgresql://host/db").

    Raises:
        StorageValidationError: If storage_url is invalid or uses unknown scheme.

    Example:
        >>> from typing import TypedDict
        >>> class User(TypedDict):
        ...     name: str
        ...     id: int
        >>> adapter = ExternalTypeAdapter(User, "postgresql://localhost/mydb")
        >>> ref = await adapter.save_external({"name": "Alice", "id": 1})
        >>> user = await adapter.load_external(ref)
    """

    def __init__(self, type_: type[T], storage_url: str) -> None:
        """Initialize the adapter with type and storage configuration.

        Validates the storage URL at construction time (fail-fast).

        Args:
            type_: The type to validate against.
            storage_url: Storage backend URL with registered scheme.

        Raises:
            StorageValidationError: If URL is invalid or scheme is unknown.
        """
        parsed = urlparse(storage_url)
        if not parsed.scheme or not parsed.netloc:
            raise StorageValidationError(
                f"Invalid storage URL '{storage_url}'. "
                f"Must be a valid URL with scheme and host (e.g., postgresql://host/db)"
            )

        registry = get_global_registry()
        if parsed.scheme not in registry.schemes:
            raise StorageValidationError(
                f"Unknown storage scheme '{parsed.scheme}'. "
                f"Registered schemes: {', '.join(registry.schemes) or '(none)'}"
            )

        self._type = type_
        self._storage_url = storage_url
        self._type_adapter: TypeAdapter[T] = TypeAdapter(type_)
        self._type_name = _get_type_name(type_)

    async def save_external(self, data: T) -> ExternalReference:
        """Validate and save data to external storage.

        Validates the data against the configured type before saving.
        Generates a new UUID for each save operation.

        Args:
            data: Data to validate and store. Must match the configured type.

        Returns:
            ExternalReference containing type name and generated UUID.

        Raises:
            StorageValidationError: If data fails type validation.
            StorageConnectionError: If storage backend is unavailable.

        Example:
            >>> ref = await adapter.save_external({"name": "Alice", "id": 1})
            >>> print(ref)
            {'class_name': 'User', 'id': '550e8400-e29b-41d4-a716-446655440000'}
        """
        try:
            validated = self._type_adapter.validate_python(data)
        except ValidationError as e:
            raise StorageValidationError(
                f"Validation failed for type '{self._type_name}': {e}"
            ) from e

        external_id = uuid4()

        registry = get_global_registry()
        backend = registry.create(self._storage_url)

        await backend.connect()
        try:
            now = datetime.now(UTC)
            serialized = self._type_adapter.dump_python(validated, mode="json")

            stored_data = {
                "data": serialized,
                "schema_version": 1,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            await backend.save(
                id=external_id,
                class_name=self._type_name,
                data=stored_data,
            )
        finally:
            await backend.disconnect()

        return {"class_name": self._type_name, "id": str(external_id)}

    async def load_external(self, reference: ExternalReference) -> T:
        """Load and validate data from external storage.

        Verifies type name matches and validates loaded data against
        the configured type.

        Args:
            reference: ExternalReference from a previous save_external call.

        Returns:
            Validated data of type T.

        Raises:
            StorageValidationError: If type name mismatches or data fails validation.
            RecordNotFoundError: If the referenced record doesn't exist.
            StorageConnectionError: If storage backend is unavailable.

        Example:
            >>> user = await adapter.load_external(ref)
            >>> print(user)
            {'name': 'Alice', 'id': 1}
        """
        class_name = reference.get("class_name")
        id_str = reference.get("id")

        if not isinstance(class_name, str):
            raise StorageValidationError(f"class_name must be a string, got {type(class_name)}")

        if class_name != self._type_name:
            raise StorageValidationError(
                f"Type mismatch: expected '{self._type_name}', got '{class_name}'"
            )

        try:
            external_id = UUID(id_str)
        except (ValueError, TypeError) as e:
            raise StorageValidationError(f"Invalid UUID format: {id_str}") from e

        registry = get_global_registry()
        backend = registry.create(self._storage_url)

        await backend.connect()
        try:
            stored_data = await backend.load(external_id, self._type_name)

            if stored_data is None:
                raise RecordNotFoundError(id=external_id, class_name=self._type_name)

            data_value = stored_data.get("data")
            if data_value is None:
                raise StorageValidationError("Stored data missing 'data' field")

            try:
                return self._type_adapter.validate_python(data_value)
            except ValidationError as e:
                raise StorageValidationError(
                    f"Loaded data failed validation for type '{self._type_name}': {e}"
                ) from e
        finally:
            await backend.disconnect()

    def save_external_sync(self, data: T) -> ExternalReference:
        """Synchronous version of save_external.

        Validates and saves data to external storage synchronously.
        Cannot be called from within an async context.

        Args:
            data: Data to validate and store. Must match the configured type.

        Returns:
            ExternalReference containing type name and generated UUID.

        Raises:
            RuntimeError: If called from within an async context.
            StorageValidationError: If data fails type validation.
            StorageConnectionError: If storage backend is unavailable.

        Example:
            >>> ref = adapter.save_external_sync({"name": "Alice", "id": 1})
        """
        return _run_sync(self.save_external(data))

    def load_external_sync(self, reference: ExternalReference) -> T:
        """Synchronous version of load_external.

        Loads and validates data from external storage synchronously.
        Cannot be called from within an async context.

        Args:
            reference: ExternalReference from a previous save operation.

        Returns:
            Validated data of type T.

        Raises:
            RuntimeError: If called from within an async context.
            StorageValidationError: If type mismatches or data fails validation.
            RecordNotFoundError: If the referenced record doesn't exist.

        Example:
            >>> user = adapter.load_external_sync(ref)
        """
        return _run_sync(self.load_external(reference))

    @property
    def type_name(self) -> str:
        """Get the canonical type name for this adapter.

        Returns:
            String representation of the configured type.

        Example:
            >>> adapter = ExternalTypeAdapter(list[User], "postgresql://...")
            >>> print(adapter.type_name)
            'list[User]'
        """
        return self._type_name
