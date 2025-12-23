"""Tests for backend registry."""

from typing import Any
from uuid import UUID

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict, register_backend
from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.registry import BackendRegistry, get_global_registry


class CustomTestBackend(StorageBackend):
    """Custom backend for testing registry functionality."""

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
        CustomTestBackend._storage[key] = data

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        key = f"{class_name}:{id}"
        return CustomTestBackend._storage.get(key)


@pytest.fixture(autouse=True)
def clear_custom_backend_storage() -> None:
    """Clear custom backend storage before each test."""
    CustomTestBackend._storage.clear()


def test_register_backend_adds_custom_scheme() -> None:
    """Test register_backend adds custom scheme."""
    registry = BackendRegistry()
    registry.register("custom", CustomTestBackend)

    assert "custom" in registry.schemes
    backend = registry.create("custom://localhost/test")
    assert isinstance(backend, CustomTestBackend)


def test_register_backend_rejects_non_storage_backend_classes() -> None:
    """Test register_backend rejects non-StorageBackend classes."""
    registry = BackendRegistry()

    class NotABackend:
        pass

    with pytest.raises(TypeError, match="must be a StorageBackend subclass"):
        registry.register("invalid", NotABackend)  # type: ignore[arg-type]


async def test_custom_backend_works_with_external_base_model() -> None:
    """Test custom backend works with ExternalBaseModel."""
    register_backend("mybackend", CustomTestBackend)

    class TestModel(ExternalBaseModel):
        name: str
        value: int

        model_config = ExternalConfigDict(storage="mybackend://localhost/test")

    original = TestModel(name="test", value=42)
    reference = await original.model_dump()

    assert "class_name" in reference
    assert "id" in reference
    assert reference["class_name"] == "TestModel"

    restored = await TestModel.model_validate(reference)
    assert restored.name == "test"
    assert restored.value == 42
    assert str(restored._external_id) == reference["id"]


def test_unknown_scheme_raises_storage_validation_error() -> None:
    """Test unknown scheme raises StorageValidationError."""
    registry = BackendRegistry()

    with pytest.raises(ValueError, match="Unknown storage scheme"):
        registry.create("unknownscheme://localhost/test")


def test_global_registry_is_singleton() -> None:
    """Test global registry returns the same instance."""
    registry1 = get_global_registry()
    registry2 = get_global_registry()

    assert registry1 is registry2


def test_registry_schemes_property_returns_sorted_list() -> None:
    """Test registry schemes property returns sorted list."""
    registry = BackendRegistry()
    registry.register("zebra", CustomTestBackend)
    registry.register("apple", CustomTestBackend)
    registry.register("mango", CustomTestBackend)

    schemes = registry.schemes
    assert schemes == ["apple", "mango", "zebra"]
