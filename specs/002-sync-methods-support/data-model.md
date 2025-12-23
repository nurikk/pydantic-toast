# Data Model: Synchronous Methods Support

**Feature**: 002-sync-methods-support
**Date**: 2025-12-23

## Entities

### ExternalBaseModel

The core entity that extends `pydantic.BaseModel` with external storage capabilities while preserving full pydantic API compatibility.

**Fields (Private Attributes)**:

| Field | Type | Description |
|-------|------|-------------|
| `_external_id` | `UUID \| None` | Unique identifier for storage; generated on first `save_external()` |
| `_storage_url` | `str \| None` | Connection URL from model_config; set during `model_post_init` |

**Pydantic Methods (Inherited, NOT Overridden)**:

| Method | Signature | Behavior |
|--------|-----------|----------|
| `model_dump` | `() -> dict[str, Any]` | Returns dict of model fields (standard pydantic) |
| `model_dump_json` | `() -> str` | Returns JSON string of model fields (standard pydantic) |
| `model_validate` | `(obj) -> Self` | Creates instance from dict/object (standard pydantic) |
| `model_validate_json` | `(json_data) -> Self` | Creates instance from JSON (standard pydantic) |

**Storage Methods (New)**:

| Method | Signature | Behavior |
|--------|-----------|----------|
| `save_external` | `async () -> dict[str, str]` | Persists to storage, returns external reference |
| `save_external_sync` | `() -> dict[str, str]` | Sync wrapper for `save_external()` |
| `load_external` | `async (reference) -> Self` | Loads from storage using external reference |
| `load_external_sync` | `(reference) -> Self` | Sync wrapper for `load_external()` |
| `is_external_reference` | `(data) -> bool` | Checks if data is external reference format |

### External Reference

Lightweight dictionary format used to reference persisted model data.

**Structure**:

```python
{
    "class_name": str,  # Model class name (e.g., "UserProfile")
    "id": str           # UUID string (e.g., "550e8400-e29b-41d4-a716-446655440000")
}
```

**Validation Rules**:
- Must have exactly 2 keys: `class_name` and `id`
- `class_name` must match the target model class
- `id` must be a valid UUID string

### StorageBackend (Unchanged)

Abstract interface for storage implementations. No changes required for this feature.

**Methods**:

| Method | Signature | Description |
|--------|-----------|-------------|
| `connect` | `async () -> None` | Establish connection to backend |
| `disconnect` | `async () -> None` | Close connection and cleanup |
| `save` | `async (id, class_name, data) -> None` | Persist data to storage |
| `load` | `async (id, class_name) -> dict \| None` | Retrieve data from storage |

## State Transitions

### Model Lifecycle

```text
                    ┌─────────────┐
                    │   Created   │
                    │ _external_id│
                    │   = None    │
                    └──────┬──────┘
                           │
                    save_external()
                           │
                           ▼
                    ┌─────────────┐
                    │   Saved     │
                    │ _external_id│◄────────┐
                    │   = UUID    │         │
                    └──────┬──────┘         │
                           │                │
              ┌────────────┴────────────┐   │
              │                         │   │
       model_dump()            save_external()
       (pydantic dict)         (updates storage)
              │                         │   │
              ▼                         └───┘
        dict[str, Any]
     (field values only)
```

### External Reference Flow

```text
┌─────────────────┐     save_external()    ┌─────────────────┐
│ ExternalBase    │ ──────────────────────►│ External Ref    │
│ Model Instance  │                        │ {"class_name",  │
└─────────────────┘                        │  "id"}          │
        ▲                                  └────────┬────────┘
        │                                           │
        │         load_external(ref)                │
        └───────────────────────────────────────────┘
```

## Validation Rules

### ExternalConfigDict Validation (Existing, Unchanged)

1. `storage` key is required
2. URL must have valid scheme and netloc
3. Scheme must be registered in BackendRegistry

### External Reference Validation

1. Must be a dict with exactly 2 keys
2. Must contain `class_name` (str) and `id` (str)
3. `class_name` must match target model's `__name__`
4. `id` must be parseable as UUID

### Sync Context Validation

1. `save_external_sync()` and `load_external_sync()` detect running event loop
2. If called within async context, raise `RuntimeError` with guidance
3. Use `asyncio.run()` for sync execution

## Relationship to Existing Entities

```text
ExternalBaseModel
       │
       │ uses
       ▼
BackendRegistry ──────► StorageBackend (abstract)
       │                       │
       │ creates               │ implements
       ▼                       ▼
   [backend instance] ◄── PostgreSQLBackend
                       ◄── RedisBackend
```

No changes to `BackendRegistry` or `StorageBackend` hierarchy.
