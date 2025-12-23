"""ExternalBaseModel and ExternalConfigDict for external storage."""

import json
from datetime import UTC, datetime
from typing import Any, TypedDict
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, PrivateAttr

from pydantic_toast.exceptions import RecordNotFoundError, StorageValidationError
from pydantic_toast.registry import get_global_registry


class ExternalConfigDict(TypedDict, total=False):
    """Configuration dictionary for external storage models.

    Extends Pydantic's ConfigDict with storage backend configuration.
    """

    storage: str


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

    @classmethod
    async def model_validate(  # type: ignore[override]
        cls, obj: Any, **kwargs: Any
    ) -> "ExternalBaseModel":
        """Validate object and restore from storage if it's an external reference."""
        if cls._is_external_reference(obj):
            storage_url: str | None = None
            config = getattr(cls, "model_config", None)
            # config can be dict or ConfigDict-like object
            if hasattr(config, "get"):
                storage_url = config.get("storage")  # type: ignore[union-attr]
            else:
                storage_url = getattr(config, "storage", None)

            if storage_url is None:
                raise StorageValidationError("Storage URL not configured")

            data = await cls._fetch_from_storage(obj, storage_url)
            instance = super().model_validate(data, **kwargs)
            instance._external_id = UUID(obj["id"])
            return instance
        return super().model_validate(obj, **kwargs)

    @classmethod
    async def model_validate_json(  # type: ignore[override]
        cls, json_data: str, **kwargs: Any
    ) -> "ExternalBaseModel":
        """Validate JSON string and restore from storage if it's an external reference."""
        import json as json_module

        obj = json_module.loads(json_data)
        return await cls.model_validate(obj, **kwargs)

    @staticmethod
    def _is_external_reference(data: Any) -> bool:
        """Check if data is an external reference format."""
        if not isinstance(data, dict):
            return False
        return "class_name" in data and "id" in data and len(data) == 2

    @classmethod
    async def _fetch_from_storage(
        cls, reference: dict[str, Any], storage_url: str
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

    async def model_dump(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        """Dump model to external reference format.

        Persists the model data to external storage and returns a lightweight
        reference containing only the class name and ID.

        Returns:
            dict: External reference in format {"class_name": "...", "id": "..."}
        """
        if self._external_id is None:
            self._external_id = uuid4()

        await self._persist_to_storage()

        return {
            "class_name": self.__class__.__name__,
            "id": str(self._external_id),
        }

    async def model_dump_json(self, **kwargs: Any) -> str:  # type: ignore[override]
        """Dump model to external reference JSON string.

        Returns:
            str: JSON string of external reference
        """
        ref = await self.model_dump(**kwargs)
        return json.dumps(ref)

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

            data = super().model_dump()

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
