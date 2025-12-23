# Research: External Storage for Pydantic Models

**Feature Branch**: `001-external-storage`  
**Date**: 2025-12-23

## Technology Decisions

### 1. Pydantic v2 Model Customization

**Decision**: Use Pydantic v2's `model_validator`, custom `ConfigDict`, and override serialization methods.

**Rationale**:
- Pydantic v2 provides clean hooks via `model_validator(mode='before')` and `model_validator(mode='after')` for intercepting validation
- `ConfigDict` can be extended to create `ExternalConfigDict` with additional storage parameters
- `model_dump()` and `model_validate()` are the primary serialization entry points and can be overridden cleanly
- Field-level `exclude=True` pattern shows Pydantic's design for controlling serialization

**Alternatives Considered**:
- Pydantic v1: Rejected - deprecated patterns, less flexible validation hooks
- Custom metaclass: Rejected - adds complexity, Pydantic's hooks are sufficient
- Wrapper functions: Rejected - doesn't integrate with Pydantic ecosystem (FastAPI, etc.)

**Implementation Notes**:
```python
class ExternalBaseModel(BaseModel):
    model_config = ExternalConfigDict(storage='...')
    
    @model_validator(mode='before')
    @classmethod
    def restore_from_storage(cls, data):
        if is_external_reference(data):
            return fetch_from_storage(data)
        return data
    
    def model_dump(self, **kwargs):
        self._persist_to_storage()
        return {"class_name": self.__class__.__name__, "id": str(self._external_id)}
```

### 2. PostgreSQL Backend: asyncpg

**Decision**: Use `asyncpg` for PostgreSQL storage backend.

**Rationale**:
- High performance async PostgreSQL driver
- Connection pooling built-in (`asyncpg.create_pool()`)
- Native Python types support (no ORM overhead)
- Prepared statements for security and performance
- Used in production by FastAPI ecosystem

**Alternatives Considered**:
- psycopg3: Good async support but asyncpg has better performance benchmarks
- SQLAlchemy: Too heavy for simple key-value storage pattern
- psycopg2: Sync-only, doesn't fit async architecture

**Schema Design**:
```sql
CREATE TABLE external_models (
    id UUID PRIMARY KEY,
    class_name VARCHAR(255) NOT NULL,
    data JSONB NOT NULL,
    schema_version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_class_name ON external_models(class_name);
```

### 3. Redis Backend: redis-py

**Decision**: Use `redis-py` with async support (`redis.asyncio`).

**Rationale**:
- Official Redis Python client
- Native async support via `redis.asyncio`
- Connection pooling built-in
- JSON support via RedisJSON or native serialization
- Widely adopted, well-documented

**Alternatives Considered**:
- aioredis: Merged into redis-py, no longer maintained separately
- redis-om-python: Object mapping adds unnecessary overhead for our use case
- hiredis: Lower level than needed

**Key Format**:
```
pydantic_toast:{class_name}:{uuid}
```

**Data Format**:
```json
{
    "data": {...},
    "schema_version": 1,
    "created_at": "2025-12-23T00:00:00Z",
    "updated_at": "2025-12-23T00:00:00Z"
}
```

### 4. Storage Backend Interface

**Decision**: Abstract base class with async methods.

**Rationale**:
- Async pattern aligns with both asyncpg and redis-py
- ABC enforces implementation of required methods
- URL scheme routing for backend selection
- Minimal interface (4 methods per SC-006)

**Interface Design**:
```python
class StorageBackend(ABC):
    @abstractmethod
    async def connect(self) -> None: ...
    
    @abstractmethod
    async def disconnect(self) -> None: ...
    
    @abstractmethod
    async def save(self, id: UUID, class_name: str, data: dict) -> None: ...
    
    @abstractmethod
    async def load(self, id: UUID, class_name: str) -> dict | None: ...
```

### 5. URL Scheme Routing

**Decision**: Parse storage URL scheme to select backend.

**Rationale**:
- Familiar pattern (SQLAlchemy, Django, etc.)
- Extensible for custom backends
- Single configuration point

**Implementation**:
```python
BACKENDS = {
    "postgresql": PostgreSQLBackend,
    "postgres": PostgreSQLBackend,
    "redis": RedisBackend,
}

def get_backend(url: str) -> StorageBackend:
    scheme = urlparse(url).scheme
    backend_cls = BACKENDS.get(scheme)
    if not backend_cls:
        raise ValueError(f"Unknown storage scheme: {scheme}")
    return backend_cls(url)
```

### 6. UUID Generation Strategy

**Decision**: Use UUID4 generated on first dump, stored as private attribute.

**Rationale**:
- UUID4 provides sufficient uniqueness without coordination
- Private attribute (`_external_id`) doesn't pollute model fields
- Generated lazily (only when dump is called)
- Preserved across multiple dumps of same instance

**Implementation**:
```python
class ExternalBaseModel(BaseModel):
    _external_id: UUID | None = PrivateAttr(default=None)
    
    def model_dump(self, **kwargs):
        if self._external_id is None:
            self._external_id = uuid4()
        # ... persist and return reference
```

### 7. Error Handling Strategy

**Decision**: Custom exception hierarchy with actionable messages.

**Rationale**:
- Clear distinction between connection, validation, and not-found errors
- Actionable error messages per SC-005
- Preserves underlying exception for debugging

**Exception Hierarchy**:
```python
class ExternalStorageError(Exception): ...
class StorageConnectionError(ExternalStorageError): ...
class RecordNotFoundError(ExternalStorageError): ...
class StorageValidationError(ExternalStorageError): ...
```

## Performance Considerations

### Latency Goals (SC-003: <50ms overhead)

- Use connection pooling for both PostgreSQL and Redis
- Lazy connection initialization (connect on first use)
- Prepared statements for PostgreSQL
- Pipeline support for Redis batch operations

### Memory Considerations

- Stream large objects if needed (future enhancement)
- No caching by default (storage is source of truth)
- Configurable serialization (JSON by default, MessagePack optional)

## Security Considerations

- Connection strings may contain credentials - never log them
- Validate class_name matches during restore (prevent class confusion attacks)
- Schema version validation to detect incompatible data

## Dependencies

```toml
[project]
dependencies = [
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
postgresql = ["asyncpg>=0.29.0"]
redis = ["redis>=5.0.0"]
all = ["asyncpg>=0.29.0", "redis>=5.0.0"]
```
