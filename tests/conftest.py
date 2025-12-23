"""Test fixtures for pydantic-toast tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID

import pytest
from testcontainers.core.container import DockerClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

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
async def clear_storage() -> AsyncGenerator[None]:
    """Clear in-memory storage before each test."""
    InMemoryBackend._storage.clear()
    yield
    InMemoryBackend._storage.clear()


@pytest.fixture(scope="function")
async def mock_storage() -> AsyncGenerator[dict[str, Any]]:
    """In-memory storage for testing without external dependencies."""
    storage: dict[str, Any] = {}
    yield storage
    storage.clear()


@pytest.fixture(scope="session", autouse=True)
def check_docker_available() -> None:
    """Check if Docker is available for testcontainers.

    Skips all tests if Docker is not running.
    """
    try:
        DockerClient().client.ping()
    except Exception as e:
        pytest.skip(f"Docker not available: {e}. Install and start Docker to run tests.")


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Provide PostgreSQL 16 container for testing.

    Container is started once per test session and shared across all tests.
    """
    container = PostgresContainer("postgres:16")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def postgres_url(postgres_container: PostgresContainer) -> str:
    """Get PostgreSQL connection URL from container.

    Returns URL without driver for asyncpg compatibility.
    """
    url: str = postgres_container.get_connection_url(driver=None)
    return url


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    """Provide Redis 7 container for testing.

    Container is started once per test session and shared across all tests.
    """
    container = RedisContainer("redis:7")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def redis_url(redis_container: RedisContainer) -> str:
    """Get Redis connection URL from container."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"
