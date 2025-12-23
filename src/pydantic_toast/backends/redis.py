import json
from typing import Any, cast
from uuid import UUID

from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.exceptions import ExternalStorageError, StorageConnectionError


class RedisBackend(StorageBackend):
    def __init__(self, url: str, key_prefix: str = "pydantic_toast") -> None:
        super().__init__(url)
        self._client: Any = None
        self._key_prefix = key_prefix

    async def connect(self) -> None:
        try:
            from redis import asyncio as aioredis
        except ImportError as e:
            raise StorageConnectionError(
                "redis is not installed. Install with: pip install pydantic-toast[redis]",
                url=self._url,
                cause=e,
            ) from e

        try:
            self._client = await aioredis.from_url(self._url)  # type: ignore[no-untyped-call]
            await self._client.ping()
        except Exception as e:
            raise StorageConnectionError(
                f"Failed to connect to Redis: {e}",
                url=self._url,
                cause=e,
            ) from e

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        if self._client is None:
            raise StorageConnectionError("Not connected to Redis", url=self._url)

        try:
            key = self._make_key(id, class_name)
            value = json.dumps(data)
            await self._client.set(key, value)
        except Exception as e:
            raise ExternalStorageError(f"Failed to save record: {e}") from e

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        if self._client is None:
            raise StorageConnectionError("Not connected to Redis", url=self._url)

        try:
            key = self._make_key(id, class_name)
            value = await self._client.get(key)
            if value is None:
                return None
            return cast(dict[str, Any], json.loads(value))
        except Exception as e:
            raise ExternalStorageError(f"Failed to load record: {e}") from e

    def _make_key(self, id: UUID, class_name: str) -> str:
        return f"{self._key_prefix}:{class_name}:{id}"
