"""ExternalBaseModel and ExternalConfigDict for external storage."""

import asyncio
from collections.abc import Coroutine
from datetime import UTC, datetime
from typing import Any, Self, TypedDict, TypeVar
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, PrivateAttr

from pydantic_toast.exceptions import RecordNotFoundError, StorageValidationError
from pydantic_toast.registry import get_global_registry

T = TypeVar("T")


class ExternalReference(TypedDict):
    """External reference format for stored models."""

    class_name: str
    id: str


class ExternalConfigDict(ConfigDict, total=False):
    """Configuration dictionary for external storage models.

    Extends Pydantic's ConfigDict with storage backend configuration.
    """

    storage: str


def _run_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run coroutine synchronously with event loop detection.

    Args:
        coro: Coroutine to execute

    Returns:
        Result of the coroutine

    Raises:
        RuntimeError: If called from within an async context
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None:
        raise RuntimeError(
            "Cannot use sync storage methods inside async context. "
            "Use the async version instead (e.g., 'await save_external()')."
        )

    return asyncio.run(coro)


class ExternalBaseModel(BaseModel):
    """Base class for Pydantic models with external storage.

    Models inheriting from this class will store their data in an external
    storage backend (PostgreSQL, Redis, or custom) rather than serializing
    all fields inline.

    Example:
        >>> class User(ExternalBaseModel):
        ...     name: str
        ...     email: str
        ...     model_config = ExternalConfigDict(storage="postgresql://localhost/db")
        >>>
        >>> user = User(name="Alice", email="alice@example.com")
        >>> ref = user.model_dump()  # Returns {"class_name": "User", "id": "..."}
    """

    _external_id: UUID | None = PrivateAttr(default=None)
    _storage_url: str | None = PrivateAttr(default=None)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate storage configuration when subclass is defined."""
        super().__init_subclass__(**kwargs)

        config = getattr(cls, "model_config", None)

        if config is None:
            raise StorageValidationError(
                f"{cls.__name__}: model_config with storage is required for ExternalBaseModel"
            )

        storage_url: str | None = None
        if isinstance(config, dict):
            storage_url = config.get("storage")
        else:
            # Must be ConfigDict or similar object
            storage_url = getattr(config, "storage", None)

        if not storage_url:
            raise StorageValidationError(f"{cls.__name__}: storage URL is required in model_config")

        parsed = urlparse(storage_url)
        if not parsed.scheme or not parsed.netloc:
            raise StorageValidationError(
                f"{cls.__name__}: Invalid storage URL '{storage_url}'. "
                f"Must be a valid URL with scheme and host (e.g., postgresql://host/db)"
            )

        registry = get_global_registry()
        if parsed.scheme not in registry.schemes:
            raise StorageValidationError(
                f"{cls.__name__}: Unknown storage scheme '{parsed.scheme}'. "
                f"Registered schemes: {', '.join(registry.schemes) or '(none)'}"
            )

    def model_post_init(self, __context: Any) -> None:
        """Initialize storage URL from model_config after instance creation."""
        super().model_post_init(__context)

        config = self.model_config
        # config can be dict or ConfigDict-like object
        if hasattr(config, "get"):
            self._storage_url = config.get("storage")  # type: ignore[assignment]
        else:
            self._storage_url = getattr(config, "storage", None)

    @staticmethod
    def _is_external_reference(data: Any) -> bool:
        """Check if data is an external reference format."""
        if not isinstance(data, dict):
            return False
        return "class_name" in data and "id" in data and len(data) == 2

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
        if not isinstance(data, dict):
            return False
        return "class_name" in data and "id" in data and len(data) == 2

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
        if self._external_id is None:
            self._external_id = uuid4()

        await self._persist_to_storage()

        return {
            "class_name": self.__class__.__name__,
            "id": str(self._external_id),
        }

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
        return _run_sync(self.save_external())

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
        storage_url: str | None = None
        config = getattr(cls, "model_config", None)
        if hasattr(config, "get"):
            storage_url = config.get("storage")  # type: ignore[union-attr]
        else:
            storage_url = getattr(config, "storage", None)

        if storage_url is None:
            raise StorageValidationError("Storage URL not configured")

        data = await cls._fetch_from_storage(reference, storage_url)
        instance = super().model_validate(data)
        instance._external_id = UUID(reference["id"])
        return instance

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
        return _run_sync(cls.load_external(reference))

    @classmethod
    async def _fetch_from_storage(
        cls, reference: ExternalReference, storage_url: str
    ) -> dict[str, Any]:
        """Fetch model data from storage using external reference."""
        class_name = reference.get("class_name")
        id_str = reference.get("id")

        if not isinstance(class_name, str):
            raise StorageValidationError(f"class_name must be a string, got {type(class_name)}")

        if class_name != cls.__name__:
            raise StorageValidationError(
                f"class_name mismatch: expected '{cls.__name__}', got '{class_name}'"
            )

        try:
            external_id = UUID(id_str)
        except (ValueError, TypeError) as e:
            raise StorageValidationError(f"Invalid UUID format: {id_str}") from e

        registry = get_global_registry()
        backend = registry.create(storage_url)

        await backend.connect()

        try:
            stored_data = await backend.load(external_id, class_name)

            if stored_data is None:
                raise RecordNotFoundError(id=external_id, class_name=class_name)

            data_field: dict[str, Any] = stored_data.get("data", {})
            return data_field
        finally:
            await backend.disconnect()

    async def _persist_to_storage(self) -> None:
        """Persist model data to configured storage backend.

        Internal helper that:
        - Connects to storage backend
        - Serializes model data with metadata
        - Saves to storage with UUID key
        """
        if self._storage_url is None:
            raise StorageValidationError("Storage URL not configured")

        if self._external_id is None:
            raise StorageValidationError("External ID not set")

        registry = get_global_registry()
        backend = registry.create(self._storage_url)

        await backend.connect()

        try:
            now = datetime.now(UTC)

            data = super().model_dump(mode="json")

            stored_data = {
                "data": data,
                "schema_version": 1,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }

            await backend.save(
                id=self._external_id,
                class_name=self.__class__.__name__,
                data=stored_data,
            )
        finally:
            await backend.disconnect()
