# Research: External TypeAdapter

**Feature**: 004-type-adapter  
**Date**: 2025-12-23  
**Status**: Complete

## Executive Summary

Research confirms that Pydantic's `TypeAdapter` provides all necessary capabilities for implementing `ExternalTypeAdapter`. The design will wrap `TypeAdapter` to add external storage capabilities while maintaining API consistency with `ExternalBaseModel`.

## Research Tasks

### 1. Pydantic TypeAdapter Capabilities

**Decision**: Use `TypeAdapter` for validation and serialization of arbitrary types.

**Rationale**:
- `TypeAdapter` supports all types in FR-011 (TypedDict, dataclasses, NamedTuple, etc.)
- `TypeAdapter.validate_python()` provides validation before save
- `TypeAdapter.dump_python(mode="json")` provides JSON-serializable output
- `TypeAdapter.validate_json()` can validate JSON strings directly
- Error handling via `pydantic.ValidationError` aligns with existing patterns

**Alternatives Considered**:
- Manual validation: Rejected - reinventing Pydantic's wheel
- Subclassing TypeAdapter: Rejected - TypeAdapter is not designed for inheritance

### 2. Type Identifier Generation

**Decision**: Use Python's type representation via `type.__name__` for simple types and a normalized string for complex types.

**Rationale**:
- Simple types (classes): `type.__name__` gives clean names like `"User"`, `"Product"`
- Generic types: `typing.get_origin()` and `typing.get_args()` to reconstruct like `"list[User]"`
- Matches spec assumption about using Python's type representation
- Enables type mismatch detection during load (FR-010)

**Implementation**:
```python
def _get_type_name(tp: type) -> str:
    origin = typing.get_origin(tp)
    if origin is None:
        return getattr(tp, '__name__', str(tp))
    args = typing.get_args(tp)
    if not args:
        return origin.__name__
    arg_names = ", ".join(_get_type_name(a) for a in args)
    return f"{origin.__name__}[{arg_names}]"
```

**Alternatives Considered**:
- Full module path: Rejected - too verbose, e.g., `mymodule.submodule.User`
- Hash-based: Rejected - not human-readable for debugging
- Pickle type: Rejected - not JSON-serializable

### 3. Storage Format Compatibility

**Decision**: Use same storage format as `ExternalBaseModel` for backend compatibility.

**Rationale**:
- Same schema: `{data: {...}, schema_version: 1, created_at: str, updated_at: str}`
- Reuses existing `StorageBackend.save()` and `StorageBackend.load()` without changes
- No backend modifications needed (SC-004)
- Backend only stores opaque JSON; validation happens at adapter level

**Storage Schema**:
```python
{
    "data": {<serialized type data>},
    "schema_version": 1,
    "created_at": "2025-12-23T10:30:00Z",
    "updated_at": "2025-12-23T10:30:00Z"
}
```

**Alternatives Considered**:
- Add `type_name` to stored data: Rejected - redundant with `class_name` in backend key
- Different schema version: Rejected - no structural difference

### 4. Sync/Async Pattern

**Decision**: Reuse existing `_run_sync()` helper from `base.py`.

**Rationale**:
- Already implements proper event loop detection
- Raises clear `RuntimeError` in async context
- Consistent error messages with existing API
- No code duplication

**Implementation**:
```python
def save_external_sync(self, data: T) -> ExternalReference:
    return _run_sync(self.save_external(data))

def load_external_sync(self, reference: ExternalReference) -> T:
    return _run_sync(self.load_external(reference))
```

**Alternatives Considered**:
- New sync implementation: Rejected - code duplication
- Greenlet-based: Rejected - adds dependency, over-engineering

### 5. API Design

**Decision**: Use instance methods with constructor injection for storage URL.

**Rationale**:
- Matches spec's `ExternalTypeAdapter(type, storage_url)` pattern
- Instance-based allows multiple adapters for different storage backends
- Constructor validates storage URL at creation time (fail-fast)
- Methods named identically to `ExternalBaseModel` (SC-003)

**API Signature**:
```python
class ExternalTypeAdapter(Generic[T]):
    def __init__(self, type_: type[T], storage_url: str) -> None: ...
    
    async def save_external(self, data: T) -> ExternalReference: ...
    async def load_external(self, reference: ExternalReference) -> T: ...
    
    def save_external_sync(self, data: T) -> ExternalReference: ...
    def load_external_sync(self, reference: ExternalReference) -> T: ...
```

**Alternatives Considered**:
- Class methods with URL in config: Rejected - less flexible
- Decorator pattern: Rejected - doesn't match existing API style
- Module-level functions: Rejected - inconsistent with OOP design

### 6. Error Handling

**Decision**: Use existing exception types with enhanced error messages.

**Rationale**:
- `StorageValidationError`: For type validation failures (before save, after load, type mismatch)
- `RecordNotFoundError`: For missing references
- Consistent with `ExternalBaseModel` behavior (SC-003)
- Clear, actionable error messages per Constitution III

**Error Scenarios**:
| Scenario | Exception | Message Pattern |
|----------|-----------|-----------------|
| Invalid data before save | `StorageValidationError` | "Validation failed for type 'X': {details}" |
| Invalid data after load | `StorageValidationError` | "Loaded data failed validation for type 'X': {details}" |
| Type mismatch on load | `StorageValidationError` | "Type mismatch: expected 'X', got 'Y'" |
| Reference not found | `RecordNotFoundError` | "Record not found: X with id=Y" |
| Invalid storage URL | `StorageValidationError` | "Invalid storage URL..." |
| Unknown storage scheme | `StorageValidationError` | "Unknown storage scheme..." |

**Alternatives Considered**:
- New exception types: Rejected - would break API consistency
- Generic exceptions: Rejected - less informative

### 7. Collection Type Support

**Decision**: Collections work automatically via TypeAdapter's native support.

**Rationale**:
- `TypeAdapter(list[Item])` validates entire list
- `TypeAdapter(dict[str, Product])` validates all keys and values
- `dump_python(mode="json")` serializes collections correctly
- No special handling needed (FR-009 satisfied by Pydantic)

**Example**:
```python
adapter = ExternalTypeAdapter(list[User], "postgresql://...")
ref = await adapter.save_external([user1, user2, user3])
users = await adapter.load_external(ref)  # Returns list[User]
```

**Alternatives Considered**:
- Manual iteration: Rejected - TypeAdapter handles this
- Separate collection adapter: Rejected - unnecessary complexity

### 8. Dataclass and NamedTuple Support

**Decision**: Native support via TypeAdapter - no special handling.

**Rationale**:
- Pydantic TypeAdapter natively validates dataclasses
- NamedTuple validated via tuple semantics
- `dump_python(mode="json")` converts to JSON-serializable dicts
- `validate_python()` reconstructs original types

**Tested Scenarios**:
- `@dataclass` classes: Validated as structured types
- `NamedTuple`: Validated as typed tuples
- Nested combinations: Supported via recursive validation

**Alternatives Considered**:
- Custom serializers: Rejected - TypeAdapter handles all cases

## Unresolved Questions

None - all technical decisions are finalized.

## Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| pydantic | >=2.0.0 | TypeAdapter, ValidationError |
| asyncpg | >=0.29.0 | PostgreSQL backend (existing) |
| redis | >=5.0.0 | Redis backend (existing) |
| aiobotocore | >=3.0.0 | S3 backend (existing) |

No new dependencies required.

## Performance Considerations

- **TypeAdapter instantiation**: Expensive; should be created once per type (documented in quickstart)
- **Validation overhead**: Minimal compared to I/O latency
- **Serialization**: `dump_python(mode="json")` is optimized for JSON output
- **Memory**: No additional memory beyond TypeAdapter's internal schema cache

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| TypeAdapter API changes | Low | Medium | Pin pydantic>=2.0.0; TypeAdapter is stable API |
| Type name collisions | Low | Low | Type names include structure (e.g., "list[User]" vs "User") |
| Complex nested types | Low | Low | Pydantic handles recursively; edge cases tested |
