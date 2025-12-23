"""Tests for PostgreSQL storage backend."""

import os
from uuid import uuid4

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.backends.postgresql import PostgreSQLBackend
from pydantic_toast.exceptions import StorageConnectionError

pytestmark = pytest.mark.skipif(
    "POSTGRES_URL" not in os.environ,
    reason="PostgreSQL not available. Set POSTGRES_URL environment variable to run these tests.",
)


@pytest.fixture
def postgres_url() -> str:
    """Get PostgreSQL connection URL from environment."""
    return os.environ.get("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/test")


@pytest.fixture
async def postgres_backend(postgres_url: str) -> PostgreSQLBackend:
    """Create and connect a PostgreSQL backend for testing."""
    backend = PostgreSQLBackend(postgres_url)
    await backend.connect()
    yield backend
    await backend.disconnect()


async def test_postgresql_backend_connect_creates_pool(postgres_url: str) -> None:
    """Test PostgreSQLBackend connect creates pool."""
    backend = PostgreSQLBackend(postgres_url)
    assert backend._pool is None

    await backend.connect()
    assert backend._pool is not None

    await backend.disconnect()


async def test_postgresql_backend_save_stores_data(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQLBackend save stores data."""
    test_id = uuid4()
    test_class = "TestModel"
    test_data = {"name": "Alice", "email": "alice@example.com", "age": 30}

    await postgres_backend.save(test_id, test_class, test_data)

    loaded_data = await postgres_backend.load(test_id, test_class)
    assert loaded_data == test_data


async def test_postgresql_backend_load_retrieves_data(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQLBackend load retrieves data."""
    test_id = uuid4()
    test_class = "UserProfile"
    test_data = {
        "username": "bob",
        "full_name": "Bob Smith",
        "is_active": True,
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["username"] == "bob"
    assert loaded_data["full_name"] == "Bob Smith"
    assert loaded_data["is_active"] is True


async def test_postgresql_backend_handles_connection_errors() -> None:
    """Test PostgreSQLBackend handles connection errors."""
    backend = PostgreSQLBackend("postgresql://invalid:invalid@localhost:9999/invalid")

    with pytest.raises(StorageConnectionError) as exc_info:
        await backend.connect()

    assert "Failed to connect to PostgreSQL" in str(exc_info.value)


async def test_full_round_trip_with_postgresql_backend(postgres_url: str) -> None:
    """Test full round-trip with PostgreSQL backend."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        age: int
        is_active: bool

        model_config = ExternalConfigDict(storage=postgres_url)

    original = UserProfile(name="Charlie", email="charlie@example.com", age=25, is_active=True)

    reference = await original.model_dump()
    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "UserProfile"

    restored = await UserProfile.model_validate(reference)
    assert restored.name == "Charlie"
    assert restored.email == "charlie@example.com"
    assert restored.age == 25
    assert restored.is_active is True
    assert str(restored._external_id) == reference["id"]
