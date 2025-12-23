"""Tests for PostgreSQL storage backend."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.backends.postgresql import PostgreSQLBackend
from pydantic_toast.exceptions import StorageConnectionError


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


async def test_postgresql_backend_saves_uuid_field(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQL backend saves and loads UUID field correctly."""
    test_id = uuid4()
    test_class = "Transaction"
    correlation_id = uuid4()
    test_data = {
        "correlation_id": str(correlation_id),
        "amount": 250.75,
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["correlation_id"] == str(correlation_id)
    assert loaded_data["amount"] == 250.75


async def test_postgresql_backend_saves_datetime_field(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQL backend saves and loads datetime field correctly."""
    test_id = uuid4()
    test_class = "Event"
    test_datetime = datetime(2024, 6, 15, 14, 30, 45, tzinfo=UTC)
    test_data = {
        "name": "Conference",
        "created_at": test_datetime.isoformat(),
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["name"] == "Conference"
    assert loaded_data["created_at"] == test_datetime.isoformat()


async def test_postgresql_backend_saves_decimal_field(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQL backend saves and loads Decimal field correctly."""
    test_id = uuid4()
    test_class = "Invoice"
    test_data = {
        "invoice_number": "INV-2024-001",
        "total": "1234.56",
        "tax": "123.46",
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["invoice_number"] == "INV-2024-001"
    assert loaded_data["total"] == "1234.56"
    assert loaded_data["tax"] == "123.46"


async def test_postgresql_backend_saves_enum_field(postgres_backend: PostgreSQLBackend) -> None:
    """Test PostgreSQL backend saves and loads Enum field correctly."""
    test_id = uuid4()
    test_class = "Account"
    test_data = {
        "username": "alice",
        "status": "active",
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["username"] == "alice"
    assert loaded_data["status"] == "active"


async def test_postgresql_backend_saves_nested_structures(
    postgres_backend: PostgreSQLBackend,
) -> None:
    """Test PostgreSQL backend saves and loads nested lists and dicts correctly."""
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

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["tags"] == ["python", "programming", "tutorial"]
    assert loaded_data["metadata"] == {"author": "Alice", "version": "1.0"}
    assert loaded_data["nested"]["level1"][0]["key"] == "value1"


async def test_full_round_trip_with_complex_types(postgres_url: str) -> None:
    """Test full round-trip with all complex types using PostgreSQL backend."""
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

        model_config = ExternalConfigDict(storage=postgres_url)

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


async def test_postgresql_backend_handles_list_of_complex_types(
    postgres_backend: PostgreSQLBackend,
) -> None:
    """Test PostgreSQL backend saves and loads lists of complex types."""
    test_id = uuid4()
    test_class = "Schedule"
    test_data = {
        "name": "Project Milestones",
        "dates": ["2024-01-15", "2024-02-20", "2024-03-10"],
        "amounts": ["100.00", "250.50", "500.75"],
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["name"] == "Project Milestones"
    assert loaded_data["dates"] == ["2024-01-15", "2024-02-20", "2024-03-10"]
    assert loaded_data["amounts"] == ["100.00", "250.50", "500.75"]


async def test_postgresql_backend_handles_timezone_aware_datetime(
    postgres_backend: PostgreSQLBackend,
) -> None:
    """Test PostgreSQL backend preserves timezone information in datetime fields."""
    test_id = uuid4()
    test_class = "Meeting"
    utc_time = datetime(2024, 9, 15, 10, 0, 0, tzinfo=UTC)
    pst_time = datetime(2024, 9, 15, 2, 0, 0, tzinfo=timezone(timedelta(hours=-8)))

    test_data = {
        "title": "Board Meeting",
        "utc_time": utc_time.isoformat(),
        "local_time": pst_time.isoformat(),
    }

    await postgres_backend.save(test_id, test_class, test_data)
    loaded_data = await postgres_backend.load(test_id, test_class)

    assert loaded_data is not None
    assert loaded_data["title"] == "Board Meeting"
    assert loaded_data["utc_time"] == utc_time.isoformat()
    assert loaded_data["local_time"] == pst_time.isoformat()
