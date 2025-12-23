"""Tests for ExternalBaseModel and ExternalConfigDict."""

import pytest

from pydantic_toast import ExternalBaseModel, ExternalConfigDict
from pydantic_toast.exceptions import StorageValidationError


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
