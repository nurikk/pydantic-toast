# Feature Specification: Synchronous Methods Support

**Feature Branch**: `002-sync-methods-support`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "Add first class support for sync methods to be 100% compatible with pydantic."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Standard Pydantic API Usage (Priority: P1)

Developers using pydantic-toast expect to use standard pydantic methods (`model_dump()`, `model_dump_json()`, `model_validate()`, `model_validate_json()`) synchronously, exactly as they would with regular pydantic models. This enables seamless integration with existing codebases and libraries that expect synchronous pydantic behavior.

**Why this priority**: This is the core value proposition - full pydantic API compatibility. Without synchronous methods, existing code cannot use pydantic-toast as a drop-in replacement for pydantic models.

**Independent Test**: Can be tested by creating an ExternalBaseModel subclass and calling standard pydantic methods synchronously (without await), verifying they work identically to pydantic.BaseModel.

**Acceptance Scenarios**:

1. **Given** an ExternalBaseModel subclass with configured storage, **When** calling `instance.model_dump()` without await, **Then** it returns a dictionary of model data (standard pydantic format, not external reference)
2. **Given** an ExternalBaseModel subclass with configured storage, **When** calling `instance.model_dump_json()` without await, **Then** it returns a JSON string of model data (standard pydantic format)
3. **Given** an ExternalBaseModel subclass and valid data, **When** calling `Model.model_validate(data)` without await, **Then** it returns a validated model instance (standard pydantic behavior)
4. **Given** an ExternalBaseModel subclass and valid JSON string, **When** calling `Model.model_validate_json(json_str)` without await, **Then** it returns a validated model instance

---

### User Story 2 - External Storage Operations (Priority: P2)

Developers need dedicated methods for external storage operations (persist to storage, restore from storage) that are clearly distinct from standard pydantic serialization. These methods handle the async storage I/O and return external references.

**Why this priority**: This is the unique value-add of pydantic-toast - external storage. However, it must not conflict with standard pydantic methods.

**Independent Test**: Can be tested by creating an ExternalBaseModel, persisting it using dedicated storage methods, and restoring it using the external reference.

**Acceptance Scenarios**:

1. **Given** an ExternalBaseModel instance, **When** calling the dedicated persist method, **Then** the model data is stored in the configured backend and an external reference is returned
2. **Given** an external reference dictionary, **When** calling the dedicated restore method, **Then** the model is reconstructed from storage with all field values intact
3. **Given** an ExternalBaseModel instance, **When** persisting and then restoring it, **Then** the restored instance has identical field values to the original

---

### User Story 3 - Mixed Sync/Async Usage (Priority: P3)

Developers working in async contexts can use async versions of storage operations for better performance, while sync contexts can use synchronous wrappers. The library supports both paradigms seamlessly.

**Why this priority**: Flexibility for different runtime contexts (sync frameworks, async frameworks, scripts, etc.)

**Independent Test**: Can be tested by performing storage operations in both sync and async contexts and verifying identical behavior.

**Acceptance Scenarios**:

1. **Given** an ExternalBaseModel in an async context, **When** using async storage methods, **Then** operations complete without blocking the event loop
2. **Given** an ExternalBaseModel in a sync context, **When** using sync storage methods, **Then** operations complete successfully using synchronous execution

---

### Edge Cases

- What happens when `model_dump()` is called but no storage persistence is needed? Returns standard pydantic dict (no storage interaction)
- What happens when storage operations fail during sync execution? Raises appropriate exception with clear error message
- What happens when an existing event loop is running during sync storage operations? Uses appropriate execution strategy (run_in_executor or asyncio.run based on context)
- What happens when calling pydantic methods in nested async contexts? Works correctly without event loop conflicts

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST preserve standard pydantic `model_dump()` behavior - returns dict of model fields synchronously
- **FR-002**: System MUST preserve standard pydantic `model_dump_json()` behavior - returns JSON string of model fields synchronously
- **FR-003**: System MUST preserve standard pydantic `model_validate()` behavior - validates and returns model instance synchronously
- **FR-004**: System MUST preserve standard pydantic `model_validate_json()` behavior - validates JSON and returns model instance synchronously
- **FR-005**: System MUST provide dedicated method(s) for async storage persistence that return external references
- **FR-006**: System MUST provide dedicated method(s) for async restoration from external references
- **FR-007**: System MUST provide sync wrapper(s) for storage operations that work in non-async contexts
- **FR-008**: System MUST handle event loop detection to avoid conflicts when running sync operations in async contexts
- **FR-009**: System MUST maintain backward compatibility with existing storage backend interface (StorageBackend abstract class)
- **FR-010**: System MUST work with all existing storage backends (PostgreSQL, Redis) without modification to backend implementations

### Key Entities

- **ExternalBaseModel**: Base class that extends pydantic.BaseModel with external storage capabilities while preserving full pydantic API compatibility
- **External Reference**: Lightweight dictionary format (`{"class_name": "...", "id": "..."}`) used to reference persisted model data
- **Storage Backend**: Abstract interface for storage implementations (PostgreSQL, Redis, custom)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All standard pydantic methods (`model_dump`, `model_dump_json`, `model_validate`, `model_validate_json`) work synchronously without await
- **SC-002**: Existing tests for pydantic behavior pass without modification (excluding tests that specifically test current async override behavior)
- **SC-003**: Storage operations (persist/restore) work correctly in both sync and async contexts
- **SC-004**: No breaking changes to the public StorageBackend interface
- **SC-005**: Models can be used interchangeably with standard pydantic.BaseModel in existing codebases expecting sync pydantic API
- **SC-006**: Documentation and method naming clearly distinguish between pydantic-compatible methods and storage-specific methods

## Assumptions

- Python's asyncio primitives are sufficient for sync/async bridging (no need for external libraries like `anyio`)
- Storage backends remain async-only internally (sync wrappers handle the bridging at the ExternalBaseModel level)
- The existing external reference format (`{"class_name": "...", "id": "..."}`) remains unchanged
- Developers understand that storage operations may block in sync contexts
