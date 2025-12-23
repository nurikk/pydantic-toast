"""Storage backend implementations."""

from pydantic_toast.backends.base import BackendRegistry, StorageBackend

__all__ = ["StorageBackend", "BackendRegistry", "PostgreSQLBackend", "RedisBackend"]


def _try_import_postgresql() -> type[StorageBackend] | None:
    """Try to import PostgreSQL backend if asyncpg is available."""
    try:
        from pydantic_toast.backends.postgresql import PostgreSQLBackend

        return PostgreSQLBackend
    except ImportError:
        return None


def _try_import_redis() -> type[StorageBackend] | None:
    """Try to import Redis backend if redis is available."""
    try:
        from pydantic_toast.backends.redis import RedisBackend

        return RedisBackend
    except ImportError:
        return None


PostgreSQLBackend = _try_import_postgresql()
RedisBackend = _try_import_redis()
