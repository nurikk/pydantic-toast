# Research: Synchronous Methods Support

**Feature**: 002-sync-methods-support
**Date**: 2025-12-23

## Problem Analysis

### Current State

The current `ExternalBaseModel` implementation overrides pydantic's core methods with async versions:

```python
async def model_dump(self, **kwargs) -> dict[str, Any]:  # OVERRIDE - breaks sync API
async def model_dump_json(self, **kwargs) -> str:        # OVERRIDE - breaks sync API
async def model_validate(cls, obj, **kwargs):            # OVERRIDE - breaks sync API
async def model_validate_json(cls, json_data, **kwargs): # OVERRIDE - breaks sync API
```

This breaks pydantic compatibility because:
1. Standard pydantic code expects these methods to be synchronous
2. Cannot use `ExternalBaseModel` as drop-in replacement for `BaseModel`
3. Libraries that call `model_dump()` synchronously will fail

### Design Decision 1: API Structure

**Decision**: Preserve pydantic's native sync methods, add dedicated storage methods

**Rationale**:
- Pydantic methods should work exactly as in `pydantic.BaseModel`
- Storage operations are a separate concern and deserve their own API
- Clear semantic distinction: serialization (pydantic) vs persistence (storage)

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| Keep async overrides, add sync wrappers | Still breaks type hints and IDE autocomplete |
| Auto-detect sync/async context | Magic behavior violates "Explicit Over Implicit" principle |
| Require all code to be async | Breaks compatibility with sync codebases |

### Design Decision 2: Storage Method Naming

**Decision**: Use `save_external()` / `load_external()` naming convention

**Rationale**:
- "External" aligns with the `ExternalBaseModel` class name
- Clear semantic: operations that interact with external storage
- `save`/`load` are standard persistence verbs (not `dump`/`validate`)
- Avoids confusion with pydantic's `model_*` namespace

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| `persist()`/`restore()` | Less intuitive, not commonly used |
| `to_storage()`/`from_storage()` | Inconsistent with pydantic's method style |
| `model_persist()`/`model_restore()` | Could confuse with pydantic's `model_*` methods |
| `external_dump()`/`external_validate()` | "dump"/"validate" are pydantic terms for different operations |

### Design Decision 3: Sync/Async Bridge Strategy

**Decision**: Use `asyncio.run()` for sync wrappers with event loop detection

**Rationale**:
- Standard Python approach for running async code in sync contexts
- Built into Python, no external dependencies needed
- Event loop detection prevents nested loop errors

**Implementation Pattern**:
```python
def save_external_sync(self) -> dict[str, Any]:
    """Sync wrapper for save_external()."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is not None:
        # Already in async context - can't use asyncio.run()
        raise RuntimeError(
            "Cannot use sync method in async context. Use 'await save_external()' instead."
        )
    return asyncio.run(self.save_external())
```

**Alternatives Considered**:

| Alternative | Rejected Because |
|-------------|------------------|
| `nest_asyncio` library | Adds external dependency; can cause subtle bugs |
| `run_in_executor` | More complex; still needs event loop management |
| Thread-based execution | Overhead for simple operations; complexity |

### Design Decision 4: Return Type for Storage Methods

**Decision**: 
- `save_external()` returns external reference dict `{"class_name": ..., "id": ...}`
- `load_external()` is a classmethod that returns model instance

**Rationale**:
- Matches current `model_dump()` behavior for external references
- Clear API: save returns what you need to restore later
- Symmetric: save returns reference, load accepts reference

**Method Signatures**:
```python
async def save_external(self) -> dict[str, str]:
    """Persist model to storage, return external reference."""
    ...

@classmethod
async def load_external(cls, reference: dict[str, str]) -> Self:
    """Load model from storage using external reference."""
    ...
```

### Design Decision 5: Backward Compatibility

**Decision**: This is a BREAKING CHANGE - document migration path

**Rationale**:
- Current API is fundamentally incompatible with pydantic
- Cannot maintain both behaviors simultaneously
- Clear migration is better than confusing hybrid state

**Migration Path**:
| Old Code | New Code |
|----------|----------|
| `await model.model_dump()` | `await model.save_external()` |
| `await Model.model_validate(ref)` | `await Model.load_external(ref)` |
| `await model.model_dump_json()` | `(await model.save_external())` → JSON separately |
| `model.model_dump()` (sync) | Works! Returns pydantic dict |

### Design Decision 6: StorageBackend Interface

**Decision**: No changes to StorageBackend abstract class

**Rationale**:
- Backend implementations remain async-only (correct for I/O operations)
- Sync bridging happens at ExternalBaseModel level
- Existing backends (PostgreSQL, Redis) work without modification

## Technical Specifications

### New Public API

```python
class ExternalBaseModel(BaseModel):
    # Pydantic methods - UNCHANGED from BaseModel
    def model_dump(self, ...) -> dict[str, Any]: ...
    def model_dump_json(self, ...) -> str: ...
    @classmethod
    def model_validate(cls, obj, ...) -> Self: ...
    @classmethod
    def model_validate_json(cls, json_data, ...) -> Self: ...
    
    # Storage methods - NEW
    async def save_external(self) -> dict[str, str]: ...
    def save_external_sync(self) -> dict[str, str]: ...
    
    @classmethod
    async def load_external(cls, reference: dict[str, str]) -> Self: ...
    @classmethod
    def load_external_sync(cls, reference: dict[str, str]) -> Self: ...
    
    # Helper - detect external reference format
    @staticmethod
    def is_external_reference(data: Any) -> bool: ...
```

### Event Loop Detection Pattern

```python
import asyncio

def _run_sync(coro):
    """Run coroutine synchronously with event loop detection."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is not None:
        raise RuntimeError(
            "Cannot use sync storage methods inside async context. "
            "Use the async version instead (e.g., 'await save_external()')."
        )
    
    return asyncio.run(coro)
```

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking change frustrates users | Clear migration guide in docs and changelog |
| Sync wrappers called in async context | RuntimeError with helpful message |
| Performance of sync wrappers | Minimal overhead - single asyncio.run() call |
| Type hint complexity | Use `Self` from typing_extensions for return types |

## Open Questions (Resolved)

All clarifications have been resolved through research:

1. ✅ **Method naming** → `save_external`/`load_external`
2. ✅ **Sync bridge strategy** → `asyncio.run()` with event loop detection
3. ✅ **Backward compatibility** → Breaking change with migration path
4. ✅ **Backend changes** → None required
