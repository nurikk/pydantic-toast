"""ExternalBaseModel and ExternalConfigDict for external storage."""

from typing import Any, TypedDict
from urllib.parse import urlparse
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, PrivateAttr

from pydantic_toast.exceptions import StorageValidationError
from pydantic_toast.registry import get_global_registry


class ExternalConfigDict(TypedDict, total=False):
    """Configuration dictionary for external storage models.
    
    Extends Pydantic's ConfigDict with storage backend configuration.
    """

    storage: str  # Required: storage backend URL


class ExternalBaseModel(BaseModel):
    """Base class for Pydantic models with external storage.
    
    Models inheriting from this class will store their data in an external
    storage backend (PostgreSQL, Redis, or custom) rather than serializing
    all fields inline.
    
    Example:
        >>> class User(ExternalBaseModel):
        ...     name: str
        ...     email: str
        ...     model_config = ExternalConfigDict(storage="postgresql://localhost/db")
        >>> 
        >>> user = User(name="Alice", email="alice@example.com")
        >>> ref = user.model_dump()  # Returns {"class_name": "User", "id": "..."}
    """

    _external_id: UUID | None = PrivateAttr(default=None)
    _storage_url: str | None = PrivateAttr(default=None)

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Validate storage configuration when subclass is defined."""
        super().__init_subclass__(**kwargs)
        
        # Get model_config from the class
        config = getattr(cls, "model_config", None)
        
        if config is None:
            raise StorageValidationError(
                f"{cls.__name__}: model_config with storage is required for ExternalBaseModel"
            )
        
        # Check if storage is specified
        storage_url = None
        if isinstance(config, dict):
            storage_url = config.get("storage")
        elif isinstance(config, ConfigDict):
            storage_url = getattr(config, "storage", None)
        
        if not storage_url:
            raise StorageValidationError(
                f"{cls.__name__}: storage URL is required in model_config"
            )
        
        # Validate URL format
        parsed = urlparse(storage_url)
        if not parsed.scheme or not parsed.netloc:
            raise StorageValidationError(
                f"{cls.__name__}: Invalid storage URL '{storage_url}'. "
                f"Must be a valid URL with scheme and host (e.g., postgresql://host/db)"
            )
        
        # Verify the scheme is registered
        registry = get_global_registry()
        if parsed.scheme not in registry.schemes:
            raise StorageValidationError(
                f"{cls.__name__}: Unknown storage scheme '{parsed.scheme}'. "
                f"Registered schemes: {', '.join(registry.schemes) or '(none)'}"
            )

    def model_post_init(self, __context: Any) -> None:
        """Initialize storage URL from model_config after instance creation."""
        super().model_post_init(__context)
        
        config = self.model_config
        if isinstance(config, dict):
            self._storage_url = config.get("storage")
        elif isinstance(config, ConfigDict):
            self._storage_url = getattr(config, "storage", None)
