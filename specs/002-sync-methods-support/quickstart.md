# Quickstart: Synchronous Methods Support

**Feature**: 002-sync-methods-support
**Date**: 2025-12-23

## Overview

This guide shows how to use `ExternalBaseModel` with the new sync-compatible API. After this update, pydantic's standard methods work synchronously (as expected), while external storage operations use dedicated methods.

## Installation

```bash
pip install pydantic-toast[postgresql]  # or [redis] or [all]
```

## Basic Usage

### Define a Model

```python
from pydantic_toast import ExternalBaseModel, ExternalConfigDict

class User(ExternalBaseModel):
    name: str
    email: str
    age: int
    
    model_config = ExternalConfigDict(storage="postgresql://localhost:5432/mydb")
```

### Pydantic API (Sync - Works Like Standard Pydantic)

```python
# Create instance
user = User(name="Alice", email="alice@example.com", age=30)

# Standard pydantic methods - NO await needed!
data = user.model_dump()
# {"name": "Alice", "email": "alice@example.com", "age": 30}

json_str = user.model_dump_json()
# '{"name": "Alice", "email": "alice@example.com", "age": 30}'

# Validation works synchronously
user2 = User.model_validate({"name": "Bob", "email": "bob@example.com", "age": 25})
user3 = User.model_validate_json('{"name": "Carol", "email": "carol@example.com", "age": 28}')
```

### Storage API (Async - For External Persistence)

```python
import asyncio

async def main():
    user = User(name="Alice", email="alice@example.com", age=30)
    
    # Save to external storage
    ref = await user.save_external()
    # {"class_name": "User", "id": "550e8400-e29b-41d4-a716-446655440000"}
    
    # Load from external storage
    restored = await User.load_external(ref)
    assert restored.name == "Alice"
    assert restored.email == "alice@example.com"

asyncio.run(main())
```

### Storage API (Sync Wrappers - For Non-Async Contexts)

```python
# In scripts, Flask routes, or other sync contexts
user = User(name="Alice", email="alice@example.com", age=30)

# Sync wrappers - NO await needed
ref = user.save_external_sync()
restored = User.load_external_sync(ref)

assert restored.name == "Alice"
```

## Migration from Previous API

If you were using the previous async `model_dump()` API:

| Old Code | New Code |
|----------|----------|
| `ref = await user.model_dump()` | `ref = await user.save_external()` |
| `user = await User.model_validate(ref)` | `user = await User.load_external(ref)` |
| `json = await user.model_dump_json()` | `ref = await user.save_external()` + `json.dumps(ref)` |
| N/A (didn't work sync) | `data = user.model_dump()` ✅ Now works! |

## Detecting External References

Use `is_external_reference()` to check if data is an external reference:

```python
from pydantic_toast import ExternalBaseModel

# Check if data is an external reference
ref = {"class_name": "User", "id": "550e8400-..."}
regular_data = {"name": "Alice", "email": "alice@example.com"}

ExternalBaseModel.is_external_reference(ref)          # True
ExternalBaseModel.is_external_reference(regular_data) # False
```

## Error Handling

### Sync Methods in Async Context

```python
async def main():
    user = User(name="Alice", email="alice@example.com", age=30)
    
    # This will raise RuntimeError!
    try:
        ref = user.save_external_sync()  # DON'T do this in async context
    except RuntimeError as e:
        print(e)  # "Cannot use sync storage methods inside async context..."
    
    # Use async version instead
    ref = await user.save_external()  # Correct!
```

### Record Not Found

```python
from pydantic_toast.exceptions import RecordNotFoundError

try:
    user = await User.load_external({
        "class_name": "User",
        "id": "00000000-0000-0000-0000-000000000000"
    })
except RecordNotFoundError as e:
    print(f"User not found: {e}")
```

### Class Name Mismatch

```python
from pydantic_toast.exceptions import StorageValidationError

class Product(ExternalBaseModel):
    name: str
    model_config = ExternalConfigDict(storage="postgresql://localhost:5432/mydb")

# Saved as User, trying to load as Product
user_ref = {"class_name": "User", "id": "550e8400-..."}

try:
    product = await Product.load_external(user_ref)
except StorageValidationError as e:
    print(e)  # "class_name mismatch: expected 'Product', got 'User'"
```

## Common Patterns

### Working with ORMs

Since pydantic methods now work synchronously, `ExternalBaseModel` integrates smoothly with ORMs:

```python
from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class UserRecord(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    profile_ref = Column(String)  # Store external reference as JSON

# Store reference in database
user = User(name="Alice", email="alice@example.com", age=30)
ref = await user.save_external()

record = UserRecord(id="user-123", profile_ref=json.dumps(ref))
session.add(record)
session.commit()

# Later: restore from reference
loaded_ref = json.loads(record.profile_ref)
user = await User.load_external(loaded_ref)
```

### API Responses

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/users")
async def create_user(name: str, email: str):
    user = User(name=name, email=email, age=0)
    ref = await user.save_external()
    return {"user_ref": ref}

@app.get("/users/{user_id}")
async def get_user(user_id: str):
    ref = {"class_name": "User", "id": user_id}
    user = await User.load_external(ref)
    return user.model_dump()  # Works synchronously!
```
