from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class StorageBackend(ABC):
    def __init__(self, url: str) -> None:
        self._url = url

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def save(
        self,
        id: UUID,
        class_name: str,
        data: dict[str, Any],
    ) -> None: ...

    @abstractmethod
    async def load(
        self,
        id: UUID,
        class_name: str,
    ) -> dict[str, Any] | None: ...


class BackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, type[StorageBackend]] = {}

    def register(self, scheme: str, backend_class: type[StorageBackend]) -> None:
        if not issubclass(backend_class, StorageBackend):
            raise TypeError(
                f"backend_class must be a StorageBackend subclass, got {backend_class.__name__}"
            )
        self._backends[scheme] = backend_class

    def create(self, url: str) -> StorageBackend:
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
        return sorted(self._backends.keys())
