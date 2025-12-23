"""Tests for ExternalBaseModel and ExternalConfigDict."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.exceptions import RecordNotFoundError, StorageValidationError

pytestmark = pytest.mark.usefixtures("register_test_backend")


def test_external_config_dict_with_valid_storage_url() -> None:
    """Test ExternalConfigDict creation with valid storage URL."""

    class TestModel(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="test://memory")

    model = TestModel(name="test")
    assert model.name == "test"


def test_external_config_dict_raises_error_for_invalid_url_format() -> None:
    """Test ExternalConfigDict raises error for invalid URL format."""
    with pytest.raises(StorageValidationError, match="Invalid storage URL"):

        class TestModel(ExternalBaseModel):
            name: str
            model_config = ExternalConfigDict(storage="not-a-valid-url")


def test_external_config_dict_raises_error_when_storage_missing() -> None:
    """Test ExternalConfigDict raises error when storage is missing."""
    with pytest.raises(StorageValidationError, match="storage.*required"):

        class TestModel(ExternalBaseModel):
            name: str
            model_config = ExternalConfigDict()  # type: ignore[call-arg]


async def test_save_external_returns_class_name_and_id_format() -> None:
    """Test save_external returns class_name and id format."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        model_config = ExternalConfigDict(storage="test://memory")

    user = UserProfile(name="Alice", email="alice@example.com")
    result = await user.save_external()

    assert "class_name" in result
    assert "id" in result
    assert result["class_name"] == "UserProfile"
    assert isinstance(result["id"], str)


async def test_save_external_generates_uuid_on_first_call() -> None:
    """Test save_external generates UUID on first call."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        model_config = ExternalConfigDict(storage="test://memory")

    product = Product(name="Widget", price=9.99)
    assert product._external_id is None

    result = await product.save_external()

    assert product._external_id is not None
    assert result["id"] == str(product._external_id)


async def test_save_external_returns_same_id_on_repeated_calls() -> None:
    """Test save_external returns same id on repeated calls."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="test://memory")

    doc = Document(title="Test", content="Content")
    result1 = await doc.save_external()
    result2 = await doc.save_external()

    assert result1["id"] == result2["id"]
    assert result1["class_name"] == result2["class_name"]


async def test_save_external_reference_can_be_serialized_to_json() -> None:
    """Test save_external reference can be serialized to JSON."""
    import json

    class Order(ExternalBaseModel):
        product: str
        quantity: int
        model_config = ExternalConfigDict(storage="test://memory")

    order = Order(product="Book", quantity=3)
    reference = await order.save_external()
    result_json = json.dumps(reference)

    result_dict = json.loads(result_json)
    assert "class_name" in result_dict
    assert "id" in result_dict
    assert result_dict["class_name"] == "Order"


def test_legacy_model_validate_still_works_for_regular_data() -> None:
    """Test model_validate still works for regular data (not external references)."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        age: int
        model_config = ExternalConfigDict(storage="test://memory")

    data = {"name": "Alice", "email": "alice@example.com", "age": 30}

    user = UserProfile.model_validate(data)

    assert user.name == "Alice"
    assert user.email == "alice@example.com"
    assert user.age == 30


def test_legacy_model_validate_json_still_works_for_regular_data() -> None:
    """Test model_validate_json still works for regular JSON data."""
    import json

    class Product(ExternalBaseModel):
        name: str
        price: float
        in_stock: bool
        model_config = ExternalConfigDict(storage="test://memory")

    data = {"name": "Widget", "price": 19.99, "in_stock": True}
    json_str = json.dumps(data)

    restored = Product.model_validate_json(json_str)

    assert restored.name == "Widget"
    assert restored.price == 19.99
    assert restored.in_stock is True


def test_model_dump_returns_dict_synchronously() -> None:
    """Test model_dump returns dict synchronously (standard pydantic behavior)."""

    class User(ExternalBaseModel):
        name: str
        email: str
        age: int
        model_config = ExternalConfigDict(storage="test://memory")

    user = User(name="Alice", email="alice@example.com", age=30)
    data = user.model_dump()

    assert isinstance(data, dict)
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert data["age"] == 30
    assert "class_name" not in data
    assert "id" not in data


def test_model_dump_json_returns_json_string_synchronously() -> None:
    """Test model_dump_json returns JSON string synchronously (standard pydantic behavior)."""
    import json

    class Product(ExternalBaseModel):
        name: str
        price: float
        model_config = ExternalConfigDict(storage="test://memory")

    product = Product(name="Widget", price=19.99)
    json_str = product.model_dump_json()

    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["name"] == "Widget"
    assert parsed["price"] == 19.99
    assert "class_name" not in parsed
    assert "id" not in parsed


def test_model_validate_creates_instance_synchronously() -> None:
    """Test model_validate creates instance synchronously (standard pydantic behavior)."""

    class Order(ExternalBaseModel):
        product: str
        quantity: int
        total: float
        model_config = ExternalConfigDict(storage="test://memory")

    data = {"product": "Book", "quantity": 3, "total": 45.99}
    order = Order.model_validate(data)

    assert isinstance(order, Order)
    assert order.product == "Book"
    assert order.quantity == 3
    assert order.total == 45.99


def test_model_validate_json_creates_instance_synchronously() -> None:
    """Test model_validate_json creates instance synchronously (standard pydantic behavior)."""
    import json

    class Document(ExternalBaseModel):
        title: str
        content: str
        author: str
        model_config = ExternalConfigDict(storage="test://memory")

    data = {"title": "Test Doc", "content": "Content here", "author": "Alice"}
    json_str = json.dumps(data)
    doc = Document.model_validate_json(json_str)

    assert isinstance(doc, Document)
    assert doc.title == "Test Doc"
    assert doc.content == "Content here"
    assert doc.author == "Alice"


async def test_save_external_persists_and_returns_reference() -> None:
    """Test save_external persists to storage and returns reference."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        age: int
        model_config = ExternalConfigDict(storage="test://memory")

    user = UserProfile(name="Alice", email="alice@example.com", age=30)
    ref = await user.save_external()

    assert "class_name" in ref
    assert "id" in ref
    assert ref["class_name"] == "UserProfile"
    assert isinstance(ref["id"], str)


async def test_load_external_restores_model_from_reference() -> None:
    """Test load_external restores model from reference."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        in_stock: bool
        model_config = ExternalConfigDict(storage="test://memory")

    original = Product(name="Widget", price=19.99, in_stock=True)
    ref = await original.save_external()

    restored = await Product.load_external(ref)

    assert restored.name == "Widget"
    assert restored.price == 19.99
    assert restored.in_stock is True


async def test_save_load_external_roundtrip_preserves_data() -> None:
    """Test save_external + load_external roundtrip preserves data."""

    class Order(ExternalBaseModel):
        product: str
        quantity: int
        total: float
        customer: str
        model_config = ExternalConfigDict(storage="test://memory")

    original = Order(product="Book", quantity=3, total=45.99, customer="Bob")
    ref = await original.save_external()

    restored = await Order.load_external(ref)

    assert restored.product == original.product
    assert restored.quantity == original.quantity
    assert restored.total == original.total
    assert restored.customer == original.customer
    assert str(restored._external_id) == ref["id"]


async def test_load_external_raises_not_found_for_invalid_id() -> None:
    """Test load_external raises RecordNotFoundError for invalid id."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="test://memory")

    ref = {"class_name": "Document", "id": "00000000-0000-0000-0000-000000000000"}

    with pytest.raises(RecordNotFoundError):
        await Document.load_external(ref)


async def test_load_external_raises_validation_error_for_class_mismatch() -> None:
    """Test load_external raises StorageValidationError for class mismatch."""

    class UserProfile(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="test://memory")

    class Product(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="test://memory")

    user = UserProfile(name="Alice")
    ref = await user.save_external()

    with pytest.raises(StorageValidationError, match="class_name.*mismatch"):
        await Product.load_external(ref)


def test_save_external_sync_works_in_sync_context() -> None:
    """Test save_external_sync works in sync context."""

    class User(ExternalBaseModel):
        name: str
        email: str
        model_config = ExternalConfigDict(storage="test://memory")

    user = User(name="Alice", email="alice@example.com")
    ref = user.save_external_sync()

    assert "class_name" in ref
    assert "id" in ref
    assert ref["class_name"] == "User"
    assert isinstance(ref["id"], str)


def test_load_external_sync_works_in_sync_context() -> None:
    """Test load_external_sync works in sync context."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        model_config = ExternalConfigDict(storage="test://memory")

    original = Product(name="Widget", price=19.99)
    ref = original.save_external_sync()

    restored = Product.load_external_sync(ref)

    assert restored.name == "Widget"
    assert restored.price == 19.99


async def test_save_external_sync_raises_error_in_async_context() -> None:
    """Test save_external_sync raises RuntimeError in async context."""

    class Order(ExternalBaseModel):
        product: str
        quantity: int
        model_config = ExternalConfigDict(storage="test://memory")

    order = Order(product="Book", quantity=3)

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        order.save_external_sync()


async def test_load_external_sync_raises_error_in_async_context() -> None:
    """Test load_external_sync raises RuntimeError in async context."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="test://memory")

    ref = {"class_name": "Document", "id": "550e8400-e29b-41d4-a716-446655440000"}

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        Document.load_external_sync(ref)


async def test_model_with_uuid_field_roundtrip() -> None:
    """Test model with UUID field saves and loads correctly."""

    class Transaction(ExternalBaseModel):
        correlation_id: UUID
        amount: float
        model_config = ExternalConfigDict(storage="test://memory")

    test_uuid = uuid4()
    original = Transaction(correlation_id=test_uuid, amount=100.50)
    ref = await original.save_external()

    restored = await Transaction.load_external(ref)

    assert restored.correlation_id == test_uuid
    assert restored.amount == 100.50


async def test_model_with_datetime_field_roundtrip() -> None:
    """Test model with datetime field (timezone-aware) saves and loads correctly."""

    class Event(ExternalBaseModel):
        name: str
        created_at: datetime
        model_config = ExternalConfigDict(storage="test://memory")

    test_datetime = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
    original = Event(name="Conference", created_at=test_datetime)
    ref = await original.save_external()

    restored = await Event.load_external(ref)

    assert restored.name == "Conference"
    assert restored.created_at == test_datetime


async def test_model_with_naive_datetime_field_roundtrip() -> None:
    """Test model with naive datetime (no timezone) saves and loads correctly."""

    class Log(ExternalBaseModel):
        message: str
        timestamp: datetime
        model_config = ExternalConfigDict(storage="test://memory")

    naive_dt = datetime(2024, 3, 10, 14, 20, 0)
    original = Log(message="System started", timestamp=naive_dt)
    ref = await original.save_external()

    restored = await Log.load_external(ref)

    assert restored.message == "System started"
    assert restored.timestamp == naive_dt


async def test_model_with_date_field_roundtrip() -> None:
    """Test model with date field saves and loads correctly."""

    class Appointment(ExternalBaseModel):
        patient_name: str
        appointment_date: date
        model_config = ExternalConfigDict(storage="test://memory")

    test_date = date(2024, 6, 15)
    original = Appointment(patient_name="John Doe", appointment_date=test_date)
    ref = await original.save_external()

    restored = await Appointment.load_external(ref)

    assert restored.patient_name == "John Doe"
    assert restored.appointment_date == test_date


async def test_model_with_time_field_roundtrip() -> None:
    """Test model with time field saves and loads correctly."""

    class Alarm(ExternalBaseModel):
        label: str
        alarm_time: time
        model_config = ExternalConfigDict(storage="test://memory")

    test_time = time(7, 30, 0)
    original = Alarm(label="Wake up", alarm_time=test_time)
    ref = await original.save_external()

    restored = await Alarm.load_external(ref)

    assert restored.label == "Wake up"
    assert restored.alarm_time == test_time


async def test_model_with_decimal_field_roundtrip() -> None:
    """Test model with Decimal field saves and loads correctly."""

    class Invoice(ExternalBaseModel):
        invoice_number: str
        total: Decimal
        tax: Decimal
        model_config = ExternalConfigDict(storage="test://memory")

    original = Invoice(
        invoice_number="INV-2024-001",
        total=Decimal("1234.56"),
        tax=Decimal("123.46"),
    )
    ref = await original.save_external()

    restored = await Invoice.load_external(ref)

    assert restored.invoice_number == "INV-2024-001"
    assert restored.total == Decimal("1234.56")
    assert restored.tax == Decimal("123.46")


async def test_model_with_enum_field_roundtrip() -> None:
    """Test model with Enum field saves and loads correctly."""

    class Status(str, Enum):
        ACTIVE = "active"
        PENDING = "pending"
        INACTIVE = "inactive"

    class Account(ExternalBaseModel):
        username: str
        status: Status
        model_config = ExternalConfigDict(storage="test://memory")

    original = Account(username="alice", status=Status.ACTIVE)
    ref = await original.save_external()

    restored = await Account.load_external(ref)

    assert restored.username == "alice"
    assert restored.status == Status.ACTIVE
    assert isinstance(restored.status, Status)


async def test_model_with_list_of_primitives_roundtrip() -> None:
    """Test model with list of primitives saves and loads correctly."""

    class Article(ExternalBaseModel):
        title: str
        tags: list[str]
        view_counts: list[int]
        model_config = ExternalConfigDict(storage="test://memory")

    original = Article(
        title="Python Tips",
        tags=["python", "programming", "tutorial"],
        view_counts=[100, 250, 350],
    )
    ref = await original.save_external()

    restored = await Article.load_external(ref)

    assert restored.title == "Python Tips"
    assert restored.tags == ["python", "programming", "tutorial"]
    assert restored.view_counts == [100, 250, 350]


async def test_model_with_dict_field_roundtrip() -> None:
    """Test model with dict field saves and loads correctly."""

    class Configuration(ExternalBaseModel):
        app_name: str
        settings: dict[str, str]
        limits: dict[str, int]
        model_config = ExternalConfigDict(storage="test://memory")

    original = Configuration(
        app_name="MyApp",
        settings={"theme": "dark", "language": "en"},
        limits={"max_users": 1000, "max_requests": 5000},
    )
    ref = await original.save_external()

    restored = await Configuration.load_external(ref)

    assert restored.app_name == "MyApp"
    assert restored.settings == {"theme": "dark", "language": "en"}
    assert restored.limits == {"max_users": 1000, "max_requests": 5000}


async def test_model_with_nested_model_roundtrip() -> None:
    """Test model with nested Pydantic model saves and loads correctly."""
    from pydantic import BaseModel

    class Address(BaseModel):
        street: str
        city: str
        zip_code: str

    class Person(ExternalBaseModel):
        name: str
        age: int
        address: Address
        model_config = ExternalConfigDict(storage="test://memory")

    address = Address(street="123 Main St", city="Springfield", zip_code="12345")
    original = Person(name="Alice", age=30, address=address)
    ref = await original.save_external()

    restored = await Person.load_external(ref)

    assert restored.name == "Alice"
    assert restored.age == 30
    assert restored.address.street == "123 Main St"
    assert restored.address.city == "Springfield"
    assert restored.address.zip_code == "12345"


async def test_model_with_optional_complex_types_roundtrip() -> None:
    """Test model with optional complex types saves and loads correctly."""

    class UserProfile(ExternalBaseModel):
        username: str
        last_login: datetime | None
        parent_id: UUID | None
        balance: Decimal | None
        model_config = ExternalConfigDict(storage="test://memory")

    original_with_values = UserProfile(
        username="alice",
        last_login=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        parent_id=uuid4(),
        balance=Decimal("99.99"),
    )
    ref1 = await original_with_values.save_external()
    restored1 = await UserProfile.load_external(ref1)

    assert restored1.username == "alice"
    assert restored1.last_login == original_with_values.last_login
    assert restored1.parent_id == original_with_values.parent_id
    assert restored1.balance == Decimal("99.99")

    original_with_nulls = UserProfile(
        username="bob",
        last_login=None,
        parent_id=None,
        balance=None,
    )
    ref2 = await original_with_nulls.save_external()
    restored2 = await UserProfile.load_external(ref2)

    assert restored2.username == "bob"
    assert restored2.last_login is None
    assert restored2.parent_id is None
    assert restored2.balance is None


async def test_model_with_all_complex_types_roundtrip() -> None:
    """Test comprehensive model with all complex types in one roundtrip."""
    from pydantic import BaseModel

    class Priority(str, Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    class Metadata(BaseModel):
        version: int
        author: str

    class ComplexModel(ExternalBaseModel):
        correlation_id: UUID
        created_at: datetime
        due_date: date
        reminder_time: time
        amount: Decimal
        priority: Priority
        tags: list[str]
        attributes: dict[str, str]
        metadata: Metadata
        model_config = ExternalConfigDict(storage="test://memory")

    test_uuid = uuid4()
    test_datetime = datetime(2024, 2, 20, 15, 45, 30, tzinfo=UTC)
    test_date = date(2024, 3, 1)
    test_time = time(9, 0, 0)

    original = ComplexModel(
        correlation_id=test_uuid,
        created_at=test_datetime,
        due_date=test_date,
        reminder_time=test_time,
        amount=Decimal("9999.99"),
        priority=Priority.HIGH,
        tags=["urgent", "important"],
        attributes={"category": "finance", "department": "sales"},
        metadata=Metadata(version=2, author="Alice"),
    )
    ref = await original.save_external()

    restored = await ComplexModel.load_external(ref)

    assert restored.correlation_id == test_uuid
    assert restored.created_at == test_datetime
    assert restored.due_date == test_date
    assert restored.reminder_time == test_time
    assert restored.amount == Decimal("9999.99")
    assert restored.priority == Priority.HIGH
    assert restored.tags == ["urgent", "important"]
    assert restored.attributes == {"category": "finance", "department": "sales"}
    assert restored.metadata.version == 2
    assert restored.metadata.author == "Alice"


async def test_model_with_list_of_complex_types_roundtrip() -> None:
    """Test model with list of complex types saves and loads correctly."""

    class Task(ExternalBaseModel):
        name: str
        due_dates: list[date]
        identifiers: list[UUID]
        amounts: list[Decimal]
        model_config = ExternalConfigDict(storage="test://memory")

    original = Task(
        name="Project Tasks",
        due_dates=[date(2024, 1, 15), date(2024, 2, 20), date(2024, 3, 10)],
        identifiers=[uuid4(), uuid4()],
        amounts=[Decimal("100.00"), Decimal("200.50"), Decimal("300.75")],
    )
    ref = await original.save_external()

    restored = await Task.load_external(ref)

    assert restored.name == "Project Tasks"
    assert restored.due_dates == original.due_dates
    assert restored.identifiers == original.identifiers
    assert restored.amounts == original.amounts


async def test_model_with_nested_dict_and_list_structures_roundtrip() -> None:
    """Test model with deeply nested dict and list structures."""

    class DataContainer(ExternalBaseModel):
        name: str
        nested_data: dict[str, list[dict[str, int]]]
        model_config = ExternalConfigDict(storage="test://memory")

    original = DataContainer(
        name="Analytics",
        nested_data={
            "metrics": [
                {"views": 100, "clicks": 10},
                {"views": 200, "clicks": 25},
            ],
            "totals": [
                {"sum": 500},
            ],
        },
    )
    ref = await original.save_external()

    restored = await DataContainer.load_external(ref)

    assert restored.name == "Analytics"
    assert restored.nested_data == original.nested_data


async def test_model_with_timezone_aware_datetime_preserves_timezone() -> None:
    """Test that timezone-aware datetime preserves timezone information."""

    class Event(ExternalBaseModel):
        name: str
        utc_time: datetime
        local_time: datetime
        model_config = ExternalConfigDict(storage="test://memory")

    utc_dt = datetime(2024, 5, 15, 10, 30, 0, tzinfo=UTC)
    pst = timezone(offset=timedelta(hours=-8))
    local_dt = datetime(2024, 5, 15, 2, 30, 0, tzinfo=pst)

    original = Event(name="Meeting", utc_time=utc_dt, local_time=local_dt)
    ref = await original.save_external()

    restored = await Event.load_external(ref)

    assert restored.name == "Meeting"
    assert restored.utc_time == utc_dt
    assert restored.local_time == local_dt
    assert restored.utc_time.tzinfo == UTC
    assert restored.local_time.tzinfo == pst
