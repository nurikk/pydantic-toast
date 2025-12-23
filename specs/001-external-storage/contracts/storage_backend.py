"""Storage Backend Interface Contract

This file defines the abstract interface that all storage backends must implement.
It serves as the contract between ExternalBaseModel and storage implementations.
"""

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class StorageBackend(ABC):
    """Abstract base class for external storage backends.

    All storage backends must implement these four methods to be compatible
    with ExternalBaseModel. The interface is intentionally minimal to make
    custom backend implementation straightforward (SC-006: <= 4 methods).

    Backends are responsible for:
    - Managing their own connections/pools
    - Serializing dict data to their native format
    - Handling their own error conditions (wrapped in ExternalStorageError)

    Example implementation:
        class MyBackend(StorageBackend):
            def __init__(self, url: str):
                super().__init__(url)
                self._client = None

            async def connect(self) -> None:
                self._client = await create_client(self._url)

            async def disconnect(self) -> None:
                await self._client.close()

            async def save(self, id: UUID, class_name: str, data: dict) -> None:
                await self._client.put(f"{class_name}:{id}", data)

            async def load(self, id: UUID, class_name: str) -> dict | None:
                return await self._client.get(f"{class_name}:{id}")
    """

    def __init__(self, url: str) -> None:
        """Initialize backend with connection URL.

        Args:
            url: Connection URL for the storage backend
        """
        self._url = url

    @abstractmethod
    async def connect(self) -> None:
        """Initialize connection to storage backend.

        This method should:
        - Establish connection/pool to the backend
        - Perform any necessary setup (create tables, etc.)
        - Be idempotent (safe to call multiple times)

        Raises:
            StorageConnectionError: If connection cannot be established
        """
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up connection resources.

        This method should:
        - Close all connections/pools
        - Release any held resources
        - Be idempotent (safe to call multiple times)
        """
        ...

    @abstractmethod
    async def save(
        self,
        id: UUID,
        class_name: str,
        data: dict[str, Any],
    ) -> None:
        """Persist model data to storage.

        Args:
            id: Unique identifier for this model instance
            class_name: Fully qualified class name of the model
            data: Dictionary of model field values (JSON-serializable)

        Raises:
            StorageConnectionError: If not connected or connection lost
            ExternalStorageError: If save operation fails

        Notes:
            - If a record with the same id exists, it should be updated
            - The implementation should store created_at on first save
            - The implementation should update updated_at on every save
            - The implementation should store schema_version (default: 1)
        """
        ...

    @abstractmethod
    async def load(
        self,
        id: UUID,
        class_name: str,
    ) -> dict[str, Any] | None:
        """Retrieve model data from storage.

        Args:
            id: Unique identifier of the model instance
            class_name: Fully qualified class name (for validation)

        Returns:
            Dictionary of model field values if found, None otherwise

        Raises:
            StorageConnectionError: If not connected or connection lost
            ExternalStorageError: If load operation fails

        Notes:
            - Return None if record not found (caller handles RecordNotFoundError)
            - The class_name parameter can be used for key construction
              and/or validation that the stored class_name matches
        """
        ...


class BackendRegistry:
    """Registry for storage backend implementations.

    Maps URL schemes to backend classes for dynamic instantiation.

    Example:
        registry = BackendRegistry()
        registry.register("postgresql", PostgreSQLBackend)
        registry.register("redis", RedisBackend)

        backend = registry.create("postgresql://localhost/db")
    """

    def __init__(self) -> None:
        self._backends: dict[str, type[StorageBackend]] = {}

    def register(self, scheme: str, backend_class: type[StorageBackend]) -> None:
        """Register a backend class for a URL scheme.

        Args:
            scheme: URL scheme (e.g., "postgresql", "redis", "custom")
            backend_class: StorageBackend subclass to instantiate

        Raises:
            TypeError: If backend_class is not a StorageBackend subclass
        """
        if not issubclass(backend_class, StorageBackend):
            raise TypeError(
                f"backend_class must be a StorageBackend subclass, got {backend_class.__name__}"
            )
        self._backends[scheme] = backend_class

    def create(self, url: str) -> StorageBackend:
        """Create a backend instance from a connection URL.

        Args:
            url: Connection URL with scheme (e.g., "postgresql://...")

        Returns:
            Configured StorageBackend instance (not yet connected)

        Raises:
            StorageValidationError: If scheme is not registered
        """
        from urllib.parse import urlparse

        scheme = urlparse(url).scheme
        backend_class = self._backends.get(scheme)

        if backend_class is None:
            registered = ", ".join(sorted(self._backends.keys())) or "(none)"
            raise ValueError(
                f"Unknown storage scheme: '{scheme}'. Registered schemes: {registered}"
            )

        return backend_class(url)

    @property
    def schemes(self) -> list[str]:
        """List of registered URL schemes."""
        return sorted(self._backends.keys())
