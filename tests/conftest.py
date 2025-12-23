"""Test fixtures for pydantic-toast tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

import pytest

from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.registry import get_global_registry


class InMemoryBackend(StorageBackend):
    """In-memory storage backend for testing."""

    _storage: dict[str, dict[str, Any]] = {}

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        key = f"{class_name}:{id}"
        InMemoryBackend._storage[key] = data

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        key = f"{class_name}:{id}"
        return InMemoryBackend._storage.get(key)


@pytest.fixture(scope="session", autouse=True)
def register_test_backend() -> None:
    """Register test backend for all tests."""
    registry = get_global_registry()
    registry.register("postgresql", InMemoryBackend)
    registry.register("postgres", InMemoryBackend)
    registry.register("redis", InMemoryBackend)
    registry.register("test", InMemoryBackend)


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Use the default event loop policy for all tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function", autouse=True)
async def clear_storage() -> AsyncGenerator[None, None]:
    """Clear in-memory storage before each test."""
    InMemoryBackend._storage.clear()
    yield
    InMemoryBackend._storage.clear()


@pytest.fixture(scope="function")
async def mock_storage() -> AsyncGenerator[dict[str, Any], None]:
    """In-memory storage for testing without external dependencies."""
    storage: dict[str, Any] = {}
    yield storage
    storage.clear()
