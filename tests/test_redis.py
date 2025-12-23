"""Tests for Redis storage backend."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

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

    reference = await original.save_external()
    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "Product"

    restored = await Product.load_external(reference)
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


async def test_redis_backend_saves_uuid_field(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads UUID field correctly."""
    test_id = uuid4()
    test_class = "Transaction"
    correlation_id = uuid4()
    test_data = {
        "correlation_id": str(correlation_id),
        "amount": 250.75,
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["correlation_id"] == str(correlation_id)
    assert loaded_data["amount"] == 250.75


async def test_redis_backend_saves_datetime_field(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads datetime field correctly."""
    test_id = uuid4()
    test_class = "Event"
    test_datetime = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
    test_data = {
        "name": "Conference",
        "created_at": test_datetime.isoformat(),
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["name"] == "Conference"
    assert loaded_data["created_at"] == test_datetime.isoformat()


async def test_redis_backend_saves_decimal_field(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads Decimal field correctly."""
    test_id = uuid4()
    test_class = "Invoice"
    test_data = {
        "invoice_number": "INV-2024-001",
        "total": "1234.56",
        "tax": "123.46",
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["invoice_number"] == "INV-2024-001"
    assert loaded_data["total"] == "1234.56"
    assert loaded_data["tax"] == "123.46"


async def test_redis_backend_saves_enum_field(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads Enum field correctly."""
    test_id = uuid4()
    test_class = "Account"
    test_data = {
        "username": "alice",
        "status": "active",
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["username"] == "alice"
    assert loaded_data["status"] == "active"


async def test_redis_backend_saves_nested_structures(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads nested lists and dicts correctly."""
    test_id = uuid4()
    test_class = "ComplexData"
    test_data = {
        "tags": ["python", "programming", "tutorial"],
        "metadata": {"author": "Alice", "version": "1.0"},
        "nested": {
            "level1": [
                {"key": "value1"},
                {"key": "value2"},
            ]
        },
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["tags"] == ["python", "programming", "tutorial"]
    assert loaded_data["metadata"] == {"author": "Alice", "version": "1.0"}
    assert loaded_data["nested"]["level1"][0]["key"] == "value1"


async def test_full_round_trip_with_complex_types_redis(redis_url: str) -> None:
    """Test full round-trip with all complex types using Redis backend."""
    from pydantic import BaseModel

    class Priority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str

    class ComplexRecord(ExternalBaseModel):
        record_id: UUID
        created_at: datetime
        due_date: date
        reminder_time: time
        amount: Decimal
        priority: Priority
        tags: list[str]
        metadata: dict[str, str]
        address: Address
        notes: str | None

        model_config = ExternalConfigDict(storage=redis_url)

    test_uuid = uuid4()
    test_datetime = datetime(2024, 7, 20, 10, 15, 30, tzinfo=UTC)
    test_date = date(2024, 8, 1)
    test_time = time(9, 30, 0)

    original = ComplexRecord(
        record_id=test_uuid,
        created_at=test_datetime,
        due_date=test_date,
        reminder_time=test_time,
        amount=Decimal("9999.99"),
        priority=Priority.HIGH,
        tags=["urgent", "important"],
        metadata={"category": "finance", "department": "sales"},
        address=Address(street="123 Main St", city="New York", zip_code="10001"),
        notes=None,
    )

    reference = await original.save_external()
    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "ComplexRecord"

    restored = await ComplexRecord.load_external(reference)
    assert restored.record_id == test_uuid
    assert restored.created_at == test_datetime
    assert restored.due_date == test_date
    assert restored.reminder_time == test_time
    assert restored.amount == Decimal("9999.99")
    assert restored.priority == Priority.HIGH
    assert restored.tags == ["urgent", "important"]
    assert restored.metadata == {"category": "finance", "department": "sales"}
    assert restored.address.street == "123 Main St"
    assert restored.address.city == "New York"
    assert restored.address.zip_code == "10001"
    assert restored.notes is None


async def test_redis_backend_handles_list_of_complex_types(redis_backend: RedisBackend) -> None:
    """Test Redis backend saves and loads lists of complex types."""
    test_id = uuid4()
    test_class = "Schedule"
    test_data = {
        "name": "Project Milestones",
        "dates": ["2024-01-15", "2024-02-20", "2024-03-10"],
        "amounts": ["100.00", "250.50", "500.75"],
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["name"] == "Project Milestones"
    assert loaded_data["dates"] == ["2024-01-15", "2024-02-20", "2024-03-10"]
    assert loaded_data["amounts"] == ["100.00", "250.50", "500.75"]


async def test_redis_backend_handles_timezone_aware_datetime(redis_backend: RedisBackend) -> None:
    """Test Redis backend preserves timezone information in datetime fields."""
    test_id = uuid4()
    test_class = "Meeting"
    utc_time = datetime(2024, 9, 15, 10, 0, 0, tzinfo=UTC)
    pst_time = datetime(2024, 9, 15, 2, 0, 0, tzinfo=timezone(timedelta(hours=-8)))

    test_data = {
        "title": "Board Meeting",
        "utc_time": utc_time.isoformat(),
        "local_time": pst_time.isoformat(),
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["title"] == "Board Meeting"
    assert loaded_data["utc_time"] == utc_time.isoformat()
    assert loaded_data["local_time"] == pst_time.isoformat()


async def test_redis_backend_handles_optional_complex_types(redis_backend: RedisBackend) -> None:
    """Test Redis backend handles optional complex types with None values."""
    test_id = uuid4()
    test_class = "UserProfile"
    test_data = {
        "username": "alice",
        "last_login": None,
        "parent_id": None,
        "balance": "99.99",
    }

    await redis_backend.save(test_id, test_class, test_data)
    loaded_data = await redis_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["username"] == "alice"
    assert loaded_data["last_login"] is None
    assert loaded_data["parent_id"] is None
    assert loaded_data["balance"] == "99.99"
