from dataclasses import dataclass
from typing import NamedTuple, TypedDict

import pytest
from pydantic import BaseModel

from pydantic_toast import ExternalTypeAdapter, RecordNotFoundError, StorageValidationError
from pydantic_toast.type_adapter import _get_type_name


class UserDict(TypedDict):
    name: str
    id: int


@dataclass
class Point:
    x: float
    y: float


class Product(BaseModel):
    id: int
    name: str
    price: float


class Coordinates(NamedTuple):
    lat: float
    lon: float


def test_get_type_name_for_simple_type():
    assert _get_type_name(int) == "int"
    assert _get_type_name(str) == "str"
    assert _get_type_name(UserDict) == "UserDict"


def test_get_type_name_for_list():
    assert _get_type_name(list[str]) == "list[str]"
    assert _get_type_name(list[Product]) == "list[Product]"


def test_get_type_name_for_dict():
    assert _get_type_name(dict[str, int]) == "dict[str, int]"
    assert _get_type_name(dict[str, Product]) == "dict[str, Product]"


def test_get_type_name_for_nested_generics():
    assert _get_type_name(list[dict[str, int]]) == "list[dict[str, int]]"
    assert _get_type_name(dict[str, list[Product]]) == "dict[str, list[Product]]"


def test_adapter_init_with_invalid_url_raises_error():
    with pytest.raises(StorageValidationError, match="Invalid storage URL"):
        ExternalTypeAdapter(UserDict, "not-a-url")


def test_adapter_init_with_missing_scheme_raises_error():
    with pytest.raises(StorageValidationError, match="Invalid storage URL"):
        ExternalTypeAdapter(UserDict, "localhost/db")


def test_adapter_init_with_unknown_scheme_raises_error(register_test_backend):
    with pytest.raises(StorageValidationError, match="Unknown storage scheme"):
        ExternalTypeAdapter(UserDict, "unknown://localhost/db")


def test_adapter_type_name_property(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    assert adapter.type_name == "UserDict"


def test_adapter_save_and_load_typed_dict(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    user: UserDict = {"name": "Alice", "id": 1}

    ref = adapter.save_external_sync(user)

    assert ref["class_name"] == "UserDict"
    assert "id" in ref

    loaded = adapter.load_external_sync(ref)
    assert loaded == user


async def test_adapter_save_and_load_typed_dict_async(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    user: UserDict = {"name": "Bob", "id": 2}

    ref = await adapter.save_external(user)

    assert ref["class_name"] == "UserDict"
    assert "id" in ref

    loaded = await adapter.load_external(ref)
    assert loaded == user


def test_adapter_save_and_load_dataclass(register_test_backend):
    adapter = ExternalTypeAdapter(Point, "test://localhost/test")
    point = Point(x=1.5, y=2.5)

    ref = adapter.save_external_sync(point)

    assert ref["class_name"] == "Point"

    loaded = adapter.load_external_sync(ref)
    assert loaded.x == point.x
    assert loaded.y == point.y


def test_adapter_save_and_load_named_tuple(register_test_backend):
    adapter = ExternalTypeAdapter(Coordinates, "test://localhost/test")
    coords = Coordinates(lat=40.7128, lon=-74.0060)

    ref = adapter.save_external_sync(coords)

    assert ref["class_name"] == "Coordinates"

    loaded = adapter.load_external_sync(ref)
    assert loaded.lat == coords.lat
    assert loaded.lon == coords.lon


def test_adapter_save_and_load_list_of_models(register_test_backend):
    adapter = ExternalTypeAdapter(list[Product], "test://localhost/test")
    products = [
        Product(id=1, name="Widget", price=9.99),
        Product(id=2, name="Gadget", price=19.99),
    ]

    ref = adapter.save_external_sync(products)

    assert ref["class_name"] == "list[Product]"

    loaded = adapter.load_external_sync(ref)
    assert len(loaded) == 2
    assert loaded[0].name == "Widget"
    assert loaded[1].name == "Gadget"


def test_adapter_save_and_load_dict_of_models(register_test_backend):
    adapter = ExternalTypeAdapter(dict[str, Product], "test://localhost/test")
    catalog = {
        "widget": Product(id=1, name="Widget", price=9.99),
        "gadget": Product(id=2, name="Gadget", price=19.99),
    }

    ref = adapter.save_external_sync(catalog)

    assert ref["class_name"] == "dict[str, Product]"

    loaded = adapter.load_external_sync(ref)
    assert "widget" in loaded
    assert loaded["widget"].name == "Widget"
    assert "gadget" in loaded


def test_adapter_save_validation_error_for_invalid_data(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    invalid_data = {"name": "Alice"}

    with pytest.raises(StorageValidationError, match="Validation failed for type"):
        adapter.save_external_sync(invalid_data)  # type: ignore[arg-type]


def test_adapter_load_validation_error_for_type_mismatch(register_test_backend):
    adapter1 = ExternalTypeAdapter(UserDict, "test://localhost/test")
    adapter2 = ExternalTypeAdapter(Point, "test://localhost/test")

    user: UserDict = {"name": "Alice", "id": 1}
    ref = adapter1.save_external_sync(user)

    with pytest.raises(StorageValidationError, match="Type mismatch"):
        adapter2.load_external_sync(ref)


def test_adapter_load_error_for_missing_record(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")

    missing_ref = {"class_name": "UserDict", "id": "00000000-0000-0000-0000-000000000000"}

    with pytest.raises(RecordNotFoundError):
        adapter.load_external_sync(missing_ref)  # type: ignore[arg-type]


def test_adapter_load_validation_error_for_invalid_uuid(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")

    invalid_ref = {"class_name": "UserDict", "id": "not-a-uuid"}

    with pytest.raises(StorageValidationError, match="Invalid UUID format"):
        adapter.load_external_sync(invalid_ref)  # type: ignore[arg-type]


def test_adapter_load_validation_error_for_invalid_class_name_type(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")

    invalid_ref = {"class_name": 123, "id": "550e8400-e29b-41d4-a716-446655440000"}

    with pytest.raises(StorageValidationError, match="class_name must be a string"):
        adapter.load_external_sync(invalid_ref)  # type: ignore[arg-type]


def test_adapter_saves_generate_unique_ids(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    user: UserDict = {"name": "Alice", "id": 1}

    ref1 = adapter.save_external_sync(user)
    ref2 = adapter.save_external_sync(user)

    assert ref1["id"] != ref2["id"]


async def test_adapter_save_external_sync_raises_error_in_async_context(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    user: UserDict = {"name": "Alice", "id": 1}

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        adapter.save_external_sync(user)


async def test_adapter_load_external_sync_raises_error_in_async_context(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    ref = {"class_name": "UserDict", "id": "550e8400-e29b-41d4-a716-446655440000"}

    with pytest.raises(RuntimeError, match="Cannot use sync storage methods inside async context"):
        adapter.load_external_sync(ref)  # type: ignore[arg-type]


def test_adapter_roundtrip_preserves_data_integrity(register_test_backend):
    adapter = ExternalTypeAdapter(UserDict, "test://localhost/test")
    original: UserDict = {"name": "Charlie", "id": 42}

    ref = adapter.save_external_sync(original)
    loaded = adapter.load_external_sync(ref)

    assert loaded == original


def test_adapter_with_nested_pydantic_models(register_test_backend):
    class OrderItem(BaseModel):
        product: Product
        quantity: int

    adapter = ExternalTypeAdapter(OrderItem, "test://localhost/test")
    item = OrderItem(product=Product(id=1, name="Widget", price=9.99), quantity=3)

    ref = adapter.save_external_sync(item)
    loaded = adapter.load_external_sync(ref)

    assert loaded.product.name == "Widget"
    assert loaded.quantity == 3


def test_adapter_with_list_of_primitives(register_test_backend):
    adapter = ExternalTypeAdapter(list[int], "test://localhost/test")
    numbers = [1, 2, 3, 4, 5]

    ref = adapter.save_external_sync(numbers)
    loaded = adapter.load_external_sync(ref)

    assert loaded == numbers


def test_adapter_with_dict_of_primitives(register_test_backend):
    adapter = ExternalTypeAdapter(dict[str, int], "test://localhost/test")
    scores = {"alice": 100, "bob": 95, "charlie": 88}

    ref = adapter.save_external_sync(scores)
    loaded = adapter.load_external_sync(ref)

    assert loaded == scores


def test_adapter_with_empty_list(register_test_backend):
    adapter = ExternalTypeAdapter(list[str], "test://localhost/test")
    empty_list: list[str] = []

    ref = adapter.save_external_sync(empty_list)
    loaded = adapter.load_external_sync(ref)

    assert loaded == []


def test_adapter_with_empty_dict(register_test_backend):
    adapter = ExternalTypeAdapter(dict[str, int], "test://localhost/test")
    empty_dict: dict[str, int] = {}

    ref = adapter.save_external_sync(empty_dict)
    loaded = adapter.load_external_sync(ref)

    assert loaded == {}
