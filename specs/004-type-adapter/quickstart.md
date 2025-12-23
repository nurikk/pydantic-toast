# Quickstart: ExternalTypeAdapter

**Feature**: 004-type-adapter  
**Date**: 2025-12-23

## Overview

`ExternalTypeAdapter` enables external storage for arbitrary Python types without requiring inheritance from `ExternalBaseModel`. Use it for TypedDicts, dataclasses, NamedTuples, collections, or any Pydantic-compatible type.

## Installation

```bash
pip install pydantic-toast[postgresql]  # or [redis], [s3], [all]
```

## Basic Usage

### TypedDict

```python
from typing import TypedDict
from pydantic_toast import ExternalTypeAdapter

class User(TypedDict):
    name: str
    id: int

adapter = ExternalTypeAdapter(User, "postgresql://localhost/mydb")

# Async usage
ref = await adapter.save_external({"name": "Alice", "id": 1})
user = await adapter.load_external(ref)

# Sync usage
ref = adapter.save_external_sync({"name": "Bob", "id": 2})
user = adapter.load_external_sync(ref)
```

### Dataclass

```python
from dataclasses import dataclass
from pydantic_toast import ExternalTypeAdapter

@dataclass
class Point:
    x: float
    y: float

adapter = ExternalTypeAdapter(Point, "redis://localhost:6379/0")

point = Point(x=1.5, y=2.5)
ref = await adapter.save_external(point)
restored = await adapter.load_external(ref)  # Returns Point instance
```

### Collections

```python
from pydantic import BaseModel
from pydantic_toast import ExternalTypeAdapter

class Product(BaseModel):
    id: int
    name: str
    price: float

# List of models
list_adapter = ExternalTypeAdapter(list[Product], "postgresql://localhost/mydb")
products = [Product(id=1, name="Widget", price=9.99), Product(id=2, name="Gadget", price=19.99)]
ref = await list_adapter.save_external(products)
restored = await list_adapter.load_external(ref)  # Returns list[Product]

# Dict of models
dict_adapter = ExternalTypeAdapter(dict[str, Product], "postgresql://localhost/mydb")
catalog = {"widget": Product(id=1, name="Widget", price=9.99)}
ref = await dict_adapter.save_external(catalog)
restored = await dict_adapter.load_external(ref)  # Returns dict[str, Product]
```

## Error Handling

```python
from pydantic_toast import ExternalTypeAdapter, StorageValidationError, RecordNotFoundError

adapter = ExternalTypeAdapter(User, "postgresql://localhost/mydb")

# Validation error before save
try:
    await adapter.save_external({"name": "Alice"})  # Missing 'id' field
except StorageValidationError as e:
    print(f"Validation failed: {e}")

# Type mismatch on load
try:
    wrong_ref = {"class_name": "WrongType", "id": "550e8400-..."}
    await adapter.load_external(wrong_ref)
except StorageValidationError as e:
    print(f"Type mismatch: {e}")

# Record not found
try:
    missing_ref = {"class_name": "User", "id": "00000000-0000-0000-0000-000000000000"}
    await adapter.load_external(missing_ref)
except RecordNotFoundError as e:
    print(f"Not found: {e}")
```

## Performance Tips

1. **Reuse adapters**: Create `ExternalTypeAdapter` once, not per-request:

```python
# Good: Create once at module level
user_adapter = ExternalTypeAdapter(User, STORAGE_URL)

async def handle_request(user_data: dict):
    return await user_adapter.save_external(user_data)

# Bad: Creates new adapter each time (expensive)
async def handle_request(user_data: dict):
    adapter = ExternalTypeAdapter(User, STORAGE_URL)  # Don't do this!
    return await adapter.save_external(user_data)
```

2. **Use async in async contexts**: The sync methods use `asyncio.run()` which creates a new event loop. Use async methods when already in an async context.

## Comparison with ExternalBaseModel

| Feature | ExternalBaseModel | ExternalTypeAdapter |
|---------|-------------------|---------------------|
| Requires inheritance | Yes | No |
| Works with TypedDict | No | Yes |
| Works with dataclass | No | Yes |
| Works with collections | Fields only | Top-level |
| Storage URL | In model_config | In constructor |
| Instance tracking | Yes (_external_id) | No (stateless) |

Use `ExternalBaseModel` when you own the type definition. Use `ExternalTypeAdapter` when:
- You can't modify the type (third-party)
- You need to store collections as top-level
- You prefer explicit storage URL injection
