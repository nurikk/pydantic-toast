# Quickstart: pydantic-toast

This guide demonstrates how to use pydantic-toast to store Pydantic model data in external storage backends.

## Installation

```bash
# Core library only
pip install pydantic-toast

# With PostgreSQL support
pip install pydantic-toast[postgresql]

# With Redis support
pip install pydantic-toast[redis]

# With all backends
pip install pydantic-toast[all]
```

## Basic Usage

### Define an External Model

```python
from pydantic_toast import ExternalBaseModel, ExternalConfigDict


class UserProfile(ExternalBaseModel):
    name: str
    email: str
    age: int

    model_config = ExternalConfigDict(storage="postgresql://user:pass@localhost:5432/mydb")
```

### Store and Retrieve Data

```python
import asyncio

async def main():
    # Create a model instance
    user = UserProfile(name="Alice", email="alice@example.com", age=30)

    # Dump returns a reference (data is stored externally)
    reference = user.model_dump()
    print(reference)
    # Output: {"class_name": "UserProfile", "id": "550e8400-e29b-41d4-a716-446655440000"}

    # Later, restore the full model from the reference
    restored_user = UserProfile.model_validate(reference)
    print(restored_user.name)  # "Alice"
    print(restored_user.email)  # "alice@example.com"

asyncio.run(main())
```

## PostgreSQL Backend

```python
from pydantic_toast import ExternalBaseModel, ExternalConfigDict


class Document(ExternalBaseModel):
    title: str
    content: str
    author: str

    model_config = ExternalConfigDict(
        storage="postgresql://postgres:password@localhost:5432/documents"
    )


async def example():
    doc = Document(title="Hello", content="World", author="Alice")
    
    # Store document
    ref = doc.model_dump()
    
    # Get JSON reference for API response
    json_ref = doc.model_dump_json()
    # '{"class_name": "Document", "id": "..."}'
    
    # Restore from JSON
    restored = Document.model_validate_json(json_ref)
```

## Redis Backend

```python
from pydantic_toast import ExternalBaseModel, ExternalConfigDict


class CacheEntry(ExternalBaseModel):
    key: str
    value: str
    ttl: int

    model_config = ExternalConfigDict(storage="redis://localhost:6379/0")


async def example():
    entry = CacheEntry(key="session", value="abc123", ttl=3600)
    
    # Store in Redis
    ref = entry.model_dump()
    
    # Restore later
    restored = CacheEntry.model_validate(ref)
```

## Custom Storage Backend

Implement your own storage backend by subclassing `StorageBackend`:

```python
from uuid import UUID
from typing import Any
from pydantic_toast import StorageBackend, register_backend


class FileBackend(StorageBackend):
    def __init__(self, url: str):
        super().__init__(url)
        self._base_path = url.replace("file://", "")

    async def connect(self) -> None:
        # Create directory if needed
        pass

    async def disconnect(self) -> None:
        # Nothing to clean up
        pass

    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        import json
        from pathlib import Path
        
        path = Path(self._base_path) / f"{class_name}_{id}.json"
        path.write_text(json.dumps(data))

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        import json
        from pathlib import Path
        
        path = Path(self._base_path) / f"{class_name}_{id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())


# Register the custom backend
register_backend("file", FileBackend)


# Use it
class MyModel(ExternalBaseModel):
    data: str

    model_config = ExternalConfigDict(storage="file:///tmp/models")
```

## Error Handling

```python
from pydantic_toast import (
    ExternalStorageError,
    StorageConnectionError,
    RecordNotFoundError,
)


async def safe_restore():
    try:
        user = UserProfile.model_validate({
            "class_name": "UserProfile",
            "id": "nonexistent-uuid"
        })
    except RecordNotFoundError as e:
        print(f"Record not found: {e.id}")
    except StorageConnectionError as e:
        print(f"Connection failed: {e}")
    except ExternalStorageError as e:
        print(f"Storage error: {e}")
```

## Integration with FastAPI

```python
from fastapi import FastAPI
from pydantic_toast import ExternalBaseModel, ExternalConfigDict

app = FastAPI()


class Order(ExternalBaseModel):
    product: str
    quantity: int
    customer_email: str

    model_config = ExternalConfigDict(storage="postgresql://...")


@app.post("/orders")
async def create_order(product: str, quantity: int, email: str):
    order = Order(product=product, quantity=quantity, customer_email=email)
    # Returns lightweight reference instead of full data
    return order.model_dump()


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    # Restore full order from storage
    order = Order.model_validate({"class_name": "Order", "id": order_id})
    return {"product": order.product, "quantity": order.quantity}
```

## Validation Workflow

```
┌─────────────────┐     model_dump()      ┌──────────────────┐
│  Model Instance │ ─────────────────────►│ External Storage │
│  (full data)    │                       │ (PostgreSQL/     │
└─────────────────┘                       │  Redis/Custom)   │
        ▲                                 └──────────────────┘
        │                                          │
        │          model_validate()                │
        └──────────────────────────────────────────┘
                   (reference → full data)

Reference format:
{"class_name": "UserProfile", "id": "550e8400-..."}
```
