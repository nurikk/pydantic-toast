# Data Model: External TypeAdapter

**Feature**: 004-type-adapter  
**Date**: 2025-12-23  
**Status**: Complete

## Entities

### ExternalTypeAdapter[T]

Generic class that wraps Pydantic's `TypeAdapter` to provide external storage capabilities.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `_type` | `type[T]` | The type to validate against | Must be valid Pydantic-compatible type |
| `_storage_url` | `str` | Storage backend URL | Must be valid URL with registered scheme |
| `_type_adapter` | `TypeAdapter[T]` | Internal Pydantic TypeAdapter | Created at initialization |
| `_type_name` | `str` | Canonical type identifier | Auto-generated from type |

**Relationships**: None (standalone class)

**State Transitions**: Stateless - each operation is independent

### ExternalReference (existing)

TypedDict for referencing stored data. Reused from `base.py`.

| Field | Type | Description |
|-------|------|-------------|
| `class_name` | `str` | Type identifier (e.g., "list[User]") |
| `id` | `str` | UUID string |

**Note**: For `ExternalTypeAdapter`, `class_name` holds the type representation, not a class name.

### StoredData (internal format)

JSON structure stored in backends. Same as `ExternalBaseModel`.

| Field | Type | Description |
|-------|------|-------------|
| `data` | `dict[str, Any]` | Serialized type data |
| `schema_version` | `int` | Always 1 |
| `created_at` | `str` | ISO 8601 timestamp |
| `updated_at` | `str` | ISO 8601 timestamp |

## Type Mappings

### Supported Types (FR-011)

| Python Type | Serialized Form | Example |
|-------------|-----------------|---------|
| `TypedDict` | `dict` | `{"name": "Alice", "id": 1}` |
| `@dataclass` | `dict` | `{"x": 1, "y": 2}` |
| `NamedTuple` | `list` | `[1, 2]` (ordered fields) |
| `list[T]` | `list` | `[{"id": 1}, {"id": 2}]` |
| `dict[K, V]` | `dict` | `{"key1": {"id": 1}}` |
| `set[T]` | `list` | `[1, 2, 3]` (unordered) |
| `BaseModel` | `dict` | `{"field": "value"}` |
| Primitives | native JSON | `42`, `"string"`, `true` |

### Type Name Generation

| Input Type | Generated Name |
|------------|----------------|
| `User` (class) | `"User"` |
| `list[User]` | `"list[User]"` |
| `dict[str, Product]` | `"dict[str, Product]"` |
| `list[dict[str, int]]` | `"list[dict[str, int]]"` |
| `int` | `"int"` |

## Validation Rules

### Constructor Validation

1. `storage_url` must be a valid URL with scheme and netloc
2. `storage_url` scheme must be registered in `BackendRegistry`
3. `type_` must be a valid Pydantic-compatible type

### Save Validation (before storage)

1. `data` must pass `TypeAdapter.validate_python(data)`
2. Validation errors wrapped in `StorageValidationError`

### Load Validation (after retrieval)

1. `reference.class_name` must match adapter's `_type_name`
2. Retrieved data must pass `TypeAdapter.validate_python()`
3. Type mismatch raises `StorageValidationError`
4. Missing record raises `RecordNotFoundError`

## Entity Diagram

```
┌─────────────────────────────────────────┐
│         ExternalTypeAdapter[T]          │
├─────────────────────────────────────────┤
│ - _type: type[T]                        │
│ - _storage_url: str                     │
│ - _type_adapter: TypeAdapter[T]         │
│ - _type_name: str                       │
├─────────────────────────────────────────┤
│ + save_external(data: T) -> ExtRef      │
│ + load_external(ref: ExtRef) -> T       │
│ + save_external_sync(data: T) -> ExtRef │
│ + load_external_sync(ref: ExtRef) -> T  │
└─────────────────────────────────────────┘
            │
            │ uses
            ▼
┌─────────────────────────────────────────┐
│           StorageBackend                │
├─────────────────────────────────────────┤
│ + save(id, class_name, data)            │
│ + load(id, class_name) -> dict | None   │
└─────────────────────────────────────────┘
            │
            │ stores
            ▼
┌─────────────────────────────────────────┐
│              StoredData                 │
├─────────────────────────────────────────┤
│   data: dict[str, Any]                  │
│   schema_version: 1                     │
│   created_at: str                       │
│   updated_at: str                       │
└─────────────────────────────────────────┘
```

## Database Schema

No new database schema required. Uses existing backend storage:

- **PostgreSQL**: `pydantic_toast.external_models` table (existing)
- **Redis**: Key pattern `{class_name}:{id}` (existing)
- **S3**: Object key `{class_name}/{id}.json` (existing)

The `class_name` column/key now stores type representations (e.g., "list[User]") in addition to class names.
