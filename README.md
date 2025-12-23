# pydantic-toast

External storage for Pydantic models - store data in PostgreSQL, Redis, or custom backends.

## Why use this?

Inspired by PostgreSQL's TOAST (The Oversized-Attribute Storage Technique), which automatically moves large column values out-of-line to keep rows small, **pydantic-toast** applies the same principle to Pydantic models.

Instead of serializing large or complex models inline (bloating JSON payloads), store them externally and pass around lightweight references. This is useful for:

- **Large nested models** that bloat API responses or message queues
- **Shared state** across distributed services (store once, reference everywhere)
- **Caching** expensive-to-compute models in Redis
- **Audit trails** with automatic `created_at`/`updated_at` timestamps
- **Database normalization** without manual foreign key management

When you serialize a model, you get a tiny reference like `{"class_name": "User", "id": "550e8400-..."}` instead of the full data. The actual model lives in PostgreSQL, Redis, or your custom backend.

## Features

- **Async-first** with synchronous wrappers for flexibility
- **PostgreSQL backend** with JSONB storage and automatic indexing
- **Redis backend** for fast caching scenarios
- **Custom backends** via simple 4-method interface
- **Automatic schema management** (tables, indexes created on connect)
- **Type-safe** with full Pydantic v2 support and strict mypy checking
- **Error handling** with detailed exception hierarchy

## Installation

```bash
# Core library only (no backends)
pip install pydantic-toast

# With PostgreSQL support
pip install pydantic-toast[postgresql]

# With Redis support
pip install pydantic-toast[redis]

# With S3 support
pip install pydantic-toast[s3]

# All backends
pip install pydantic-toast[all]
```

Requires Python 3.13+

## Quick Start

### Define a model with external storage

```python
from pydantic_toast import ExternalBaseModel, ExternalConfigDict

class User(ExternalBaseModel):
    name: str
    email: str
    age: int
    
    model_config = ExternalConfigDict(
        storage="postgresql://localhost/mydb"
    )
```

### Save and load (async)

```python
# Create and save
user = User(name="Alice", email="alice@example.com", age=30)
ref = await user.save_external()
print(ref)  # {"class_name": "User", "id": "550e8400-e29b-41d4-a716-446655440000"}

# Load from reference
loaded = await User.load_external(ref)
print(loaded.name)  # "Alice"
```

### Sync API

```python
# Same operations without await
user = User(name="Bob", email="bob@example.com", age=25)
ref = user.save_external_sync()  # No await needed

loaded = User.load_external_sync(ref)
print(loaded.name)  # "Bob"
```

### Check if data is a reference

```python
data = {"class_name": "User", "id": "550e8400-..."}
if ExternalBaseModel.is_external_reference(data):
    user = await User.load_external(data)
```

## Supported Backends

### PostgreSQL

Stores models in a `external_models` table with JSONB column for efficient querying.

```python
class Product(ExternalBaseModel):
    name: str
    price: float
    
    model_config = ExternalConfigDict(
        storage="postgresql://user:pass@localhost:5432/mydb"
    )
```

**Features:**
- Automatic table creation with optimized indexes
- JSONB storage for flexible querying
- Connection pooling via asyncpg
- Schema versioning support

**Table schema:**
```sql
CREATE TABLE external_models (
    id UUID PRIMARY KEY,
    class_name TEXT NOT NULL,
    data JSONB NOT NULL,
    schema_version INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### Redis

Stores models as JSON strings with predictable key format: `pydantic_toast:ClassName:uuid`

```python
class Session(ExternalBaseModel):
    user_id: str
    token: str
    expires_at: str
    
    model_config = ExternalConfigDict(
        storage="redis://localhost:6379/0"
    )
```

**Features:**
- Fast in-memory storage
- Ideal for caching and temporary data
- Async support via redis-py
- Custom key prefix support

### S3

Stores models as JSON objects in S3 buckets with key format: `{prefix}/{ClassName}/{uuid}.json`

```python
class Document(ExternalBaseModel):
    content: str
    metadata: dict
    
    model_config = ExternalConfigDict(
        storage="s3://my-bucket/models"
    )
```

**Features:**
- Object storage for large models
- Cross-region/cross-service access
- Async support via aiobotocore
- Custom endpoint support (LocalStack, MinIO)

**Key format:**
- With prefix: `models/Document/550e8400-e29b-41d4-a716-446655440000.json`
- Without prefix: `Document/550e8400-e29b-41d4-a716-446655440000.json`

## Custom Backends

Implement your own storage backend by subclassing `StorageBackend` and implementing 4 methods:

```python
from pydantic_toast import StorageBackend, register_backend
from uuid import UUID
from typing import Any
from pathlib import Path
from urllib.parse import urlparse
import json

class FileSystemBackend(StorageBackend):
    async def connect(self) -> None:
        # Initialize base directory
        self.base_path = Path(urlparse(self._url).path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def disconnect(self) -> None:
        # No cleanup needed for filesystem
        pass
    
    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        # Save to file: /base/ClassName/uuid.json
        path = self.base_path / class_name / f"{id}.json"
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(data))
    
    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        # Load from file
        path = self.base_path / class_name / f"{id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

# Register the backend
register_backend("file", FileSystemBackend)

# Use it
class Document(ExternalBaseModel):
    content: str
    model_config = ExternalConfigDict(storage="file:///tmp/models")
```

## API Reference

### `ExternalBaseModel`

Base class for models with external storage.

**Methods:**
- `save_external() -> ExternalReference` - Save to storage (async)
- `save_external_sync() -> ExternalReference` - Save to storage (sync)
- `load_external(reference: ExternalReference) -> ExternalBaseModel` - Load from storage (async)
- `load_external_sync(reference: ExternalReference) -> ExternalBaseModel` - Load from storage (sync)
- `is_external_reference(data: Any) -> bool` - Check if dict is external reference

### `ExternalConfigDict`

Configuration dictionary extending Pydantic's `ConfigDict`.

**Fields:**
- `storage: str` - Storage backend URL (required)

### `ExternalReference`

TypedDict returned by `save_external()`.

**Fields:**
- `class_name: str` - Model class name
- `id: str` - UUID identifier

### `StorageBackend`

Abstract base class for storage backends.

**Methods to implement:**
- `connect() -> None` - Initialize connection
- `disconnect() -> None` - Cleanup resources
- `save(id: UUID, class_name: str, data: dict) -> None` - Persist model
- `load(id: UUID, class_name: str) -> dict | None` - Retrieve model

### `register_backend(scheme: str, backend_class: type[StorageBackend])`

Register a custom storage backend for a URL scheme.

### Exceptions

- `ExternalStorageError` - Base exception for all storage errors
- `StorageConnectionError` - Connection failures (includes sanitized URL)
- `RecordNotFoundError` - Record not found during load (includes id and class_name)
- `StorageValidationError` - Configuration or validation errors

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests (requires PostgreSQL and Redis via testcontainers)
pytest

# Type checking
mypy src/pydantic_toast

# Linting
ruff check src/ tests/
```

## License

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

See the Unlicense for more details: <https://unlicense.org/>
