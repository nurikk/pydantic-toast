# Data Model: External Storage for Pydantic Models

**Feature Branch**: `001-external-storage`  
**Date**: 2025-12-23

## Entity Definitions

### ExternalReference

Lightweight reference returned by `model_dump()` that identifies stored data.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| class_name | str | Fully qualified class name | Required, non-empty |
| id | str | UUID as string | Required, valid UUID format |

**Validation Rules**:
- `class_name` must match the model class being validated
- `id` must be a valid UUID v4 string

### StoredModelData

Internal structure persisted to storage backends.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| id | UUID | Unique identifier | Primary key |
| class_name | str | Fully qualified class name | Required, indexed |
| data | dict | Serialized model fields | Required, JSON-serializable |
| schema_version | int | Data schema version | Required, >= 1 |
| created_at | datetime | Creation timestamp | Required, UTC |
| updated_at | datetime | Last update timestamp | Required, UTC |

**Validation Rules**:
- `schema_version` must be positive integer
- `created_at` <= `updated_at`
- `data` must be valid JSON

### ExternalConfigDict

Configuration for external storage behavior.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| storage | str | Connection URL | Required, valid URL format |
| (inherited) | ... | All Pydantic ConfigDict fields | Pydantic defaults |

**Supported URL Schemes**:
- `postgresql://` or `postgres://` - PostgreSQL backend
- `redis://` - Redis backend
- Custom schemes via backend registration

### StorageBackend (Abstract)

Interface all storage backends must implement.

| Method | Signature | Description |
|--------|-----------|-------------|
| connect | `async def connect() -> None` | Initialize connection/pool |
| disconnect | `async def disconnect() -> None` | Clean up resources |
| save | `async def save(id: UUID, class_name: str, data: dict) -> None` | Persist model data |
| load | `async def load(id: UUID, class_name: str) -> dict \| None` | Retrieve model data |

### PostgreSQLBackend

PostgreSQL implementation of StorageBackend.

| Attribute | Type | Description |
|-----------|------|-------------|
| _pool | asyncpg.Pool | Connection pool |
| _url | str | Connection URL |
| _table_name | str | Table name (default: `external_models`) |

**PostgreSQL Schema**:
```sql
CREATE TABLE external_models (
    id UUID PRIMARY KEY,
    class_name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_external_models_class_name ON external_models(class_name);
```

### RedisBackend

Redis implementation of StorageBackend.

| Attribute | Type | Description |
|-----------|------|-------------|
| _client | redis.asyncio.Redis | Redis client |
| _url | str | Connection URL |
| _key_prefix | str | Key prefix (default: `pydantic_toast`) |

**Redis Key Pattern**:
```
{key_prefix}:{class_name}:{uuid}
```

**Redis Value Format** (JSON string):
```json
{
    "data": { ... },
    "schema_version": 1,
    "created_at": "2025-12-23T00:00:00Z",
    "updated_at": "2025-12-23T00:00:00Z"
}
```

## Entity Relationships

```
ExternalBaseModel (user-defined)
    │
    ├── uses ──► ExternalConfigDict (configuration)
    │                │
    │                └── references ──► StorageBackend (abstract)
    │                                       │
    │                                       ├── PostgreSQLBackend
    │                                       │
    │                                       └── RedisBackend
    │
    ├── dumps to ──► ExternalReference (serialized output)
    │
    └── persists as ──► StoredModelData (in storage)
```

## State Transitions

### Model Instance Lifecycle

```
[New Instance] ─── model_dump() ───► [Persisted]
      │                                    │
      │                                    │
      └────── model_dump() again ──────────┤
                                           │
                                    [Updated in Storage]
```

### Storage Connection Lifecycle

```
[Uninitialized] ─── connect() ───► [Connected]
       │                                │
       │                                ├── save() / load()
       │                                │
       └────── disconnect() ◄───────────┘
                    │
                    ▼
              [Disconnected]
```

## Exception Hierarchy

```
ExternalStorageError (base)
    │
    ├── StorageConnectionError
    │       Raised when: connection fails, timeout, auth error
    │       Contains: original exception, connection URL (sanitized)
    │
    ├── RecordNotFoundError
    │       Raised when: load() finds no matching record
    │       Contains: id, class_name
    │
    └── StorageValidationError
            Raised when: class_name mismatch, invalid URL scheme
            Contains: expected value, actual value
```
