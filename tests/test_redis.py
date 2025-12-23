"""Tests for Redis storage backend."""

from uuid import uuid4

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.backends.redis import RedisBackend
from pydantic_toast.exceptions import StorageConnectionError


@pytest.fixture
async def redis_backend(redis_url: str) -> RedisBackend:
    """Create and connect a Redis backend for testing."""
    backend = RedisBackend(redis_url)
    await backend.connect()
    await backend._client.flushdb()
    yield backend
    await backend._client.flushdb()
    await backend.disconnect()


async def test_redis_backend_connect_creates_client(redis_url: str) -> None:
    """Test RedisBackend connect creates client."""
    backend = RedisBackend(redis_url)
    assert backend._client is None

    await backend.connect()
    assert backend._client is not None

    await backend.disconnect()


async def test_redis_backend_save_stores_data(redis_backend: RedisBackend) -> None:
    """Test RedisBackend save stores data."""
    test_id = uuid4()
    test_class = "TestModel"
    test_data = {"name": "Alice", "email": "alice@example.com", "age": 30}

    await redis_backend.save(test_id, test_class, test_data)

    loaded_data = await redis_backend.load(test_id, test_class)
    assert loaded_data == test_data


async def test_redis_backend_load_retrieves_data(redis_backend: RedisBackend) -> None:
    """Test RedisBackend load retrieves data."""
    test_id = uuid4()
    test_class = "CacheEntry"
    test_data = {
        "key": "session_123",
        "value": "abc123xyz",
        "ttl": 3600,
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["key"] == "session_123"
    assert loaded_data["value"] == "abc123xyz"
    assert loaded_data["ttl"] == 3600


async def test_redis_backend_key_format_is_predictable(redis_backend: RedisBackend) -> None:
    """Test RedisBackend key format is predictable."""
    test_id = uuid4()
    test_class = "Product"
    expected_key = f"pydantic_toast:{test_class}:{test_id}"

    actual_key = redis_backend._make_key(test_id, test_class)
    assert actual_key == expected_key


async def test_full_round_trip_with_redis_backend(redis_url: str) -> None:
    """Test full round-trip with Redis backend."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        in_stock: bool
        category: str

        model_config = ExternalConfigDict(storage=redis_url)

    backend = RedisBackend(redis_url)
    await backend.connect()
    await backend._client.flushdb()

    original = Product(name="Laptop", price=999.99, in_stock=True, category="Electronics")

    reference = await original.model_dump()
    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "Product"

    restored = await Product.model_validate(reference)
    assert restored.name == "Laptop"
    assert restored.price == 999.99
    assert restored.in_stock is True
    assert restored.category == "Electronics"
    assert str(restored._external_id) == reference["id"]

    await backend._client.flushdb()
    await backend.disconnect()


async def test_redis_backend_handles_connection_errors() -> None:
    """Test RedisBackend handles connection errors."""
    backend = RedisBackend("redis://invalid:9999")

    with pytest.raises(StorageConnectionError) as exc_info:
        await backend.connect()

    assert "Failed to connect to Redis" in str(exc_info.value)
