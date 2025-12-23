from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_toast.backends.base import StorageBackend

_global_registry: "BackendRegistry | None" = None


class BackendRegistry:
    def __init__(self) -> None:
        self._backends: dict[str, type[StorageBackend]] = {}

    def register(self, scheme: str, backend_class: type["StorageBackend"]) -> None:
        from pydantic_toast.backends.base import StorageBackend

        if not issubclass(backend_class, StorageBackend):
            raise TypeError(
                f"backend_class must be a StorageBackend subclass, got {backend_class.__name__}"
            )
        self._backends[scheme] = backend_class

    def create(self, url: str) -> "StorageBackend":
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


def get_global_registry() -> BackendRegistry:
    global _global_registry
    if _global_registry is None:
        _global_registry = BackendRegistry()
    return _global_registry


def register_backend(scheme: str, backend_class: type["StorageBackend"]) -> None:
    registry = get_global_registry()
    registry.register(scheme, backend_class)


def _register_builtin_backends() -> None:
    registry = get_global_registry()

    try:
        from pydantic_toast.backends.postgresql import PostgreSQLBackend

        registry.register("postgresql", PostgreSQLBackend)
        registry.register("postgres", PostgreSQLBackend)
    except ImportError:
        pass

    try:
        from pydantic_toast.backends.redis import RedisBackend

        registry.register("redis", RedisBackend)
    except ImportError:
        pass

    try:
        from pydantic_toast.backends.s3 import S3Backend

        registry.register("s3", S3Backend)
    except ImportError:
        pass


_register_builtin_backends()
