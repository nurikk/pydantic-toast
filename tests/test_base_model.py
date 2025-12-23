"""Tests for ExternalBaseModel and ExternalConfigDict."""

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.exceptions import RecordNotFoundError, StorageValidationError


def test_external_config_dict_with_valid_storage_url() -> None:
    """Test ExternalConfigDict creation with valid storage URL."""

    class TestModel(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    ref = {"class_name": "Document", "id": "00000000-0000-0000-0000-000000000000"}

    with pytest.raises(RecordNotFoundError):
        await Document.load_external(ref)


async def test_load_external_raises_validation_error_for_class_mismatch() -> None:
    """Test load_external raises StorageValidationError for class mismatch."""

    class UserProfile(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    class Product(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    user = UserProfile(name="Alice")
    ref = await user.save_external()

    with pytest.raises(StorageValidationError, match="class_name.*mismatch"):
        await Product.load_external(ref)


def test_save_external_sync_works_in_sync_context() -> None:
    """Test save_external_sync works in sync context."""

    class User(ExternalBaseModel):
        name: str
        email: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

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
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

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
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    order = Order(product="Book", quantity=3)

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        order.save_external_sync()


async def test_load_external_sync_raises_error_in_async_context() -> None:
    """Test load_external_sync raises RuntimeError in async context."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

    ref = {"class_name": "Document", "id": "550e8400-e29b-41d4-a716-446655440000"}

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        Document.load_external_sync(ref)
