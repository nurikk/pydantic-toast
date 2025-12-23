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


async def test_model_dump_returns_class_name_and_id_format() -> None:
    """Test model_dump returns class_name and id format."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    user = UserProfile(name="Alice", email="alice@example.com")
    result = await user.model_dump()

    assert "class_name" in result
    assert "id" in result
    assert result["class_name"] == "UserProfile"
    assert isinstance(result["id"], str)


async def test_model_dump_generates_uuid_on_first_call() -> None:
    """Test model_dump generates UUID on first call."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

    product = Product(name="Widget", price=9.99)
    assert product._external_id is None

    result = await product.model_dump()

    assert product._external_id is not None
    assert result["id"] == str(product._external_id)


async def test_model_dump_returns_same_id_on_repeated_calls() -> None:
    """Test model_dump returns same id on repeated calls."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    doc = Document(title="Test", content="Content")
    result1 = await doc.model_dump()
    result2 = await doc.model_dump()

    assert result1["id"] == result2["id"]
    assert result1["class_name"] == result2["class_name"]


async def test_model_dump_json_returns_json_string_of_reference() -> None:
    """Test model_dump_json returns JSON string of reference."""
    import json

    class Order(ExternalBaseModel):
        product: str
        quantity: int
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

    order = Order(product="Book", quantity=3)
    result_json = await order.model_dump_json()

    result_dict = json.loads(result_json)
    assert "class_name" in result_dict
    assert "id" in result_dict
    assert result_dict["class_name"] == "Order"


async def test_model_validate_restores_full_model_from_reference() -> None:
    """Test model_validate restores full model from reference."""

    class UserProfile(ExternalBaseModel):
        name: str
        email: str
        age: int
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    original = UserProfile(name="Alice", email="alice@example.com", age=30)
    reference = await original.model_dump()

    restored = await UserProfile.model_validate(reference)

    assert restored.name == "Alice"
    assert restored.email == "alice@example.com"
    assert restored.age == 30
    assert str(restored._external_id) == reference["id"]


async def test_model_validate_json_restores_from_json_reference() -> None:
    """Test model_validate_json restores from JSON reference."""

    class Product(ExternalBaseModel):
        name: str
        price: float
        in_stock: bool
        model_config = ExternalConfigDict(storage="redis://localhost:6379/0")

    original = Product(name="Widget", price=19.99, in_stock=True)
    reference_json = await original.model_dump_json()

    restored = await Product.model_validate_json(reference_json)

    assert restored.name == "Widget"
    assert restored.price == 19.99
    assert restored.in_stock is True


async def test_record_not_found_error_for_nonexistent_uuid() -> None:
    """Test RecordNotFoundError for nonexistent UUID."""

    class Document(ExternalBaseModel):
        title: str
        content: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    with pytest.raises(RecordNotFoundError) as exc_info:
        await Document.model_validate(
            {
                "class_name": "Document",
                "id": "00000000-0000-0000-0000-000000000000",
            }
        )

    assert "00000000-0000-0000-0000-000000000000" in str(exc_info.value)


async def test_storage_validation_error_for_class_name_mismatch() -> None:
    """Test StorageValidationError for class_name mismatch."""

    class UserProfile(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    class Product(ExternalBaseModel):
        name: str
        model_config = ExternalConfigDict(storage="postgresql://localhost:5432/test")

    user = UserProfile(name="Alice")
    reference = await user.model_dump()

    with pytest.raises(StorageValidationError, match="class_name.*mismatch"):
        await Product.model_validate(reference)
