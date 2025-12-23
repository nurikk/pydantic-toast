"""Tests for S3 storage backend."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.backends.s3 import S3Backend
from pydantic_toast.exceptions import StorageConnectionError


@pytest.fixture
async def s3_backend(s3_url: str, s3_endpoint_url: str) -> S3Backend:
    """Create and connect an S3 backend for testing."""
    backend = S3Backend(s3_url, endpoint_url=s3_endpoint_url)
    await backend.connect()
    yield backend
    await backend.disconnect()


async def test_s3_backend_connect_creates_client(s3_url: str, s3_endpoint_url: str) -> None:
    """Test S3Backend connect creates client."""
    backend = S3Backend(s3_url, endpoint_url=s3_endpoint_url)
    assert backend._client is None

    await backend.connect()
    assert backend._client is not None

    await backend.disconnect()


async def test_s3_backend_save_stores_data(s3_backend: S3Backend) -> None:
    """Test S3Backend save stores data."""
    test_id = uuid4()
    test_class = "TestModel"
    test_data = {"name": "Alice", "email": "alice@example.com", "age": 30}

    await s3_backend.save(test_id, test_class, test_data)

    loaded_data = await s3_backend.load(test_id, test_class)
    assert loaded_data == test_data


async def test_s3_backend_load_retrieves_data(s3_backend: S3Backend) -> None:
    """Test S3Backend load retrieves data."""
    test_id = uuid4()
    test_class = "UserProfile"
    test_data = {
        "username": "bob",
        "full_name": "Bob Smith",
        "is_active": True,
    }

    await s3_backend.save(test_id, test_class, test_data)
    loaded_data = await s3_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["username"] == "bob"
    assert loaded_data["full_name"] == "Bob Smith"
    assert loaded_data["is_active"] is True


async def test_s3_backend_load_returns_none_for_missing(s3_backend: S3Backend) -> None:
    """Test S3Backend load returns None for missing keys."""
    test_id = uuid4()
    test_class = "NonExistent"

    loaded_data = await s3_backend.load(test_id, test_class)
    assert loaded_data is None


async def test_s3_backend_key_format_is_predictable(s3_backend: S3Backend) -> None:
    """Test S3Backend generates predictable object keys."""
    test_id = UUID("12345678-1234-5678-1234-567812345678")
    test_class = "Product"

    key = s3_backend._make_key(test_id, test_class)
    assert key == "Product/12345678-1234-5678-1234-567812345678.json"


async def test_s3_backend_key_format_with_prefix(s3_endpoint_url: str) -> None:
    """Test S3Backend generates keys with prefix."""
    backend = S3Backend("s3://test-bucket/my-prefix", endpoint_url=s3_endpoint_url)

    test_id = UUID("12345678-1234-5678-1234-567812345678")
    test_class = "Product"

    key = backend._make_key(test_id, test_class)
    assert key == "my-prefix/Product/12345678-1234-5678-1234-567812345678.json"


async def test_s3_backend_handles_missing_bucket_errors(s3_endpoint_url: str) -> None:
    """Test S3Backend handles missing bucket errors."""
    backend = S3Backend("s3://nonexistent-bucket-xyz", endpoint_url=s3_endpoint_url)

    with pytest.raises(StorageConnectionError) as exc_info:
        await backend.connect()

    assert "does not exist" in str(exc_info.value)


async def test_s3_backend_handles_connection_errors() -> None:
    """Test S3Backend handles connection errors."""
    backend = S3Backend("s3://test-bucket", endpoint_url="http://invalid-endpoint:9999")

    with pytest.raises(StorageConnectionError) as exc_info:
        await backend.connect()

    assert "Failed to connect to S3" in str(exc_info.value)


async def test_full_round_trip_with_s3_backend(s3_url: str) -> None:
    """Test full round-trip with S3 backend."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        age: int
        is_active: bool

        model_config = ExternalConfigDict(storage=s3_url)

    original = UserProfile(name="Charlie", email="charlie@example.com", age=25, is_active=True)

    reference = await original.save_external()
    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "UserProfile"

    restored = await UserProfile.load_external(reference)
    assert restored.name == "Charlie"
    assert restored.email == "charlie@example.com"
    assert restored.age == 25
    assert restored.is_active is True
    assert str(restored._external_id) == reference["id"]


async def test_s3_backend_saves_uuid_field(s3_backend: S3Backend) -> None:
    """Test S3Backend saves UUID field."""
    test_id = uuid4()
    test_class = "UUIDModel"
    record_id = uuid4()
    test_data = {"record_id": str(record_id)}

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["record_id"] == str(record_id)


async def test_s3_backend_saves_datetime_field(s3_backend: S3Backend) -> None:
    """Test S3Backend saves datetime field."""
    test_id = uuid4()
    test_class = "DateTimeModel"
    now = datetime.now(UTC)
    test_data = {"created_at": now.isoformat()}

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["created_at"] == now.isoformat()


async def test_s3_backend_saves_decimal_field(s3_backend: S3Backend) -> None:
    """Test S3Backend saves Decimal field."""
    test_id = uuid4()
    test_class = "DecimalModel"
    test_data = {"amount": "123.45"}

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["amount"] == "123.45"


async def test_s3_backend_saves_enum_field(s3_backend: S3Backend) -> None:
    """Test S3Backend saves Enum field."""
    test_id = uuid4()
    test_class = "EnumModel"
    test_data = {"status": "active"}

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["status"] == "active"


async def test_s3_backend_saves_nested_structures(s3_backend: S3Backend) -> None:
    """Test S3Backend saves nested structures."""
    test_id = uuid4()
    test_class = "NestedModel"
    test_data = {
        "metadata": {"tags": ["important", "urgent"], "count": 42},
        "address": {"street": "Main St", "city": "Springfield"},
    }

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["metadata"]["tags"] == ["important", "urgent"]
    assert loaded["metadata"]["count"] == 42
    assert loaded["address"]["street"] == "Main St"


async def test_full_round_trip_with_complex_types_s3(s3_url: str) -> None:
    """Test full round-trip with complex types."""

    class Priority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str | None = None

    class Task(ExternalBaseModel):
        record_id: UUID
        created_at: datetime
        due_date: date
        reminder_time: time
        amount: Decimal
        priority: Priority
        tags: list[str]
        metadata: dict[str, int]
        address: Address
        notes: str | None = None

        model_config = ExternalConfigDict(storage=s3_url)

    original = Task(
        record_id=uuid4(),
        created_at=datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC),
        due_date=date(2025, 2, 1),
        reminder_time=time(9, 0),
        amount=Decimal("999.99"),
        priority=Priority.HIGH,
        tags=["work", "urgent"],
        metadata={"views": 42, "likes": 7},
        address=Address(street="123 Main St", city="Portland", zip_code="97201"),
        notes=None,
    )

    reference = await original.save_external()
    restored = await Task.load_external(reference)

    assert restored.record_id == original.record_id
    assert restored.created_at == original.created_at
    assert restored.due_date == original.due_date
    assert restored.reminder_time == original.reminder_time
    assert restored.amount == original.amount
    assert restored.priority == Priority.HIGH
    assert restored.tags == ["work", "urgent"]
    assert restored.metadata == {"views": 42, "likes": 7}
    assert restored.address.street == "123 Main St"
    assert restored.address.city == "Portland"
    assert restored.address.zip_code == "97201"
    assert restored.notes is None


async def test_s3_backend_handles_list_of_complex_types(s3_backend: S3Backend) -> None:
    """Test S3Backend handles list of complex types."""
    test_id = uuid4()
    test_class = "ListModel"
    test_data = {
        "items": [
            {"id": str(uuid4()), "name": "Item 1"},
            {"id": str(uuid4()), "name": "Item 2"},
        ]
    }

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert len(loaded["items"]) == 2
    assert loaded["items"][0]["name"] == "Item 1"
    assert loaded["items"][1]["name"] == "Item 2"


async def test_s3_backend_handles_timezone_aware_datetime(s3_backend: S3Backend) -> None:
    """Test S3Backend handles timezone-aware datetime."""
    test_id = uuid4()
    test_class = "TimezoneModel"
    utc_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=UTC)
    pst_time = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone(timedelta(hours=-8)))

    test_data = {
        "utc_time": utc_time.isoformat(),
        "pst_time": pst_time.isoformat(),
    }

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["utc_time"] == utc_time.isoformat()
    assert loaded["pst_time"] == pst_time.isoformat()


async def test_s3_backend_handles_optional_complex_types(s3_backend: S3Backend) -> None:
    """Test S3Backend handles optional complex types."""
    test_id = uuid4()
    test_class = "OptionalModel"
    test_data = {
        "required_field": "value",
        "optional_uuid": None,
        "optional_datetime": None,
        "optional_list": None,
    }

    await s3_backend.save(test_id, test_class, test_data)
    loaded = await s3_backend.load(test_id, test_class)

    assert loaded is not None
    assert loaded["required_field"] == "value"
    assert loaded["optional_uuid"] is None
    assert loaded["optional_datetime"] is None
    assert loaded["optional_list"] is None
