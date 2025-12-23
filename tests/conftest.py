"""Test fixtures for pydantic-toast tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID

import pytest
from testcontainers.core.container import DockerClient
from testcontainers.localstack import LocalStackContainer
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


@pytest.fixture(scope="session")
def register_test_backend() -> None:
    """Register InMemoryBackend for base model tests.

    This fixture should ONLY be used in test_base_model.py to test
    ExternalBaseModel functionality without real backends.

    Backend-specific tests (test_postgresql.py, test_redis.py, test_s3.py)
    should NOT use this fixture - they should use real backends via testcontainers.
    """
    registry = get_global_registry()
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
def postgres_container() -> Generator[PostgresContainer]:
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
def redis_container() -> Generator[RedisContainer]:
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


@pytest.fixture(scope="session")
def localstack_container() -> Generator[LocalStackContainer]:
    """Provide LocalStack container for S3 testing.

    Container is started once per test session and shared across all tests.
    """
    container = LocalStackContainer("localstack/localstack:3")
    container.with_services("s3")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def s3_url(localstack_container: LocalStackContainer) -> str:
    """Get S3 URL with pre-created test bucket.

    Creates a test bucket and returns s3://bucket-name URL.
    Sets AWS environment variables for aiobotocore to use the LocalStack endpoint.
    """
    import boto3

    endpoint_url = localstack_container.get_url()

    os.environ["AWS_ENDPOINT_URL"] = endpoint_url
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # noqa: S105
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",  # noqa: S106
        region_name="us-east-1",
    )
    bucket_name = "test-pydantic-toast"
    s3_client.create_bucket(Bucket=bucket_name)

    return f"s3://{bucket_name}"


@pytest.fixture(scope="session")
def s3_endpoint_url(localstack_container: LocalStackContainer) -> str:
    """Get LocalStack S3 endpoint URL for direct backend configuration."""
    url: str = localstack_container.get_url()
    return url
