# Feature Specification: External Storage for Pydantic Models

**Feature Branch**: `001-external-storage`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "Build Python library for storing data externally as Pydantic AI extension with PostgreSQL and Redis backends"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Define External Model with Storage Backend (Priority: P1)

A developer wants to define a Pydantic model that automatically stores its data in an external storage system rather than serializing all fields inline.

**Why this priority**: This is the foundational capability - without the ability to define external models and configure storage, no other functionality works.

**Independent Test**: Can be fully tested by defining an `ExternalBaseModel` subclass with `ExternalConfigDict`, instantiating it, and verifying the model accepts the configuration.

**Acceptance Scenarios**:

1. **Given** a class inheriting from `ExternalBaseModel` with `model_config = ExternalConfigDict(storage='postgresql://...')`, **When** the class is defined, **Then** the storage backend is configured and validated without errors
2. **Given** a class with an invalid storage URL format, **When** the class is defined, **Then** a clear validation error is raised indicating the URL format issue
3. **Given** a class without specifying storage in `ExternalConfigDict`, **When** the class is defined, **Then** a clear error indicates storage configuration is required

---

### User Story 2 - Serialize Model to External Reference (Priority: P1)

A developer wants to dump a model instance and receive a lightweight reference (class name + UUID) instead of the full data, with the actual data persisted to the configured storage.

**Why this priority**: This is core functionality - the primary value proposition of the library is replacing full serialization with external storage references.

**Independent Test**: Can be tested by creating an instance of an external model, calling `model_dump()`, and verifying the return contains only `class_name` and `id` while data exists in storage.

**Acceptance Scenarios**:

1. **Given** an instance of `ExternalFoo(field='aaa', field2='bbb')`, **When** `model_dump()` is called, **Then** the result is `{"class_name": "ExternalFoo", "id": "<uuid>"}` and data is stored in the backend
2. **Given** an instance that has already been dumped, **When** `model_dump()` is called again, **Then** the same `id` is returned (idempotent) and data is updated in storage
3. **Given** a storage backend that is unreachable, **When** `model_dump()` is called, **Then** an appropriate storage error is raised with connection details

---

### User Story 3 - Restore Model from External Reference (Priority: P1)

A developer wants to restore a full model instance from a serialized reference by querying the storage backend.

**Why this priority**: Without restoration, stored data cannot be retrieved - this completes the round-trip functionality.

**Independent Test**: Can be tested by validating a JSON reference string and verifying the returned object has all original field values.

**Acceptance Scenarios**:

1. **Given** a JSON string `{"class_name": "ExternalFoo", "id": "<uuid>"}`, **When** `ExternalFoo.model_validate_json(json_str)` is called, **Then** a fully hydrated `ExternalFoo` instance is returned with original field values
2. **Given** a reference with a valid UUID that does not exist in storage, **When** `model_validate_json` is called, **Then** a clear error indicates the record was not found
3. **Given** a reference with mismatched class name, **When** `ExternalFoo.model_validate_json` is called with `{"class_name": "ExternalBar", ...}`, **Then** a validation error indicates class name mismatch

---

### User Story 4 - PostgreSQL Storage Backend (Priority: P2)

A developer wants to use PostgreSQL as the storage backend for external models.

**Why this priority**: PostgreSQL is a widely-used production database; supporting it enables real-world usage.

**Independent Test**: Can be tested with a PostgreSQL instance by storing and retrieving model data.

**Acceptance Scenarios**:

1. **Given** `model_config = ExternalConfigDict(storage='postgresql://user:pass@host:5432/db')`, **When** a model is dumped, **Then** data is stored in PostgreSQL in a structured format
2. **Given** a PostgreSQL connection string with SSL parameters, **When** a model is configured, **Then** the connection uses SSL as specified
3. **Given** multiple model classes with the same storage configuration, **When** models are dumped, **Then** each class's data is stored separately and retrievable independently

---

### User Story 5 - Redis Storage Backend (Priority: P2)

A developer wants to use Redis as the storage backend for external models.

**Why this priority**: Redis provides fast in-memory storage suitable for caching and high-performance scenarios.

**Independent Test**: Can be tested with a Redis instance by storing and retrieving model data.

**Acceptance Scenarios**:

1. **Given** `model_config = ExternalConfigDict(storage='redis://host:6379/0')`, **When** a model is dumped, **Then** data is stored in Redis as a serialized value
2. **Given** a Redis connection with authentication, **When** a model is configured with `redis://:password@host:6379`, **Then** the connection authenticates successfully
3. **Given** a Redis backend, **When** a model is dumped, **Then** the key format is predictable and includes class name and UUID

---

### User Story 6 - Add Custom Storage Backend (Priority: P3)

A developer wants to implement a custom storage backend (e.g., S3, MongoDB, file system) by following a clear interface.

**Why this priority**: Extensibility enables adoption in diverse environments but is not required for initial functionality.

**Independent Test**: Can be tested by implementing a mock backend following the interface and using it with an external model.

**Acceptance Scenarios**:

1. **Given** a custom class implementing the storage backend interface, **When** registered with the library, **Then** external models can use it via a custom URL scheme
2. **Given** an incomplete backend implementation (missing required methods), **When** registration is attempted, **Then** a clear error lists the missing methods
3. **Given** a registered custom backend, **When** `model_config = ExternalConfigDict(storage='custom://...')` is used, **Then** the custom backend handles storage and retrieval

---

### Edge Cases

- What happens when the same model instance is modified and dumped multiple times? Data is updated in storage, same ID retained.
- How does the system handle concurrent access to the same stored record? Backend-specific behavior (PostgreSQL uses transactions, Redis uses atomic operations).
- What happens if storage schema/format changes between versions? Migration responsibility lies with the user; library provides version field in stored data.
- How are nested external models handled? Each external model is stored independently with its own reference.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide `ExternalBaseModel` base class that extends Pydantic's `BaseModel`
- **FR-002**: System MUST provide `ExternalConfigDict` for configuring storage backend via connection URL
- **FR-003**: System MUST override `model_dump()` to return `{"class_name": str, "id": str}` format
- **FR-004**: System MUST override `model_dump_json()` to return JSON string of the reference format
- **FR-005**: System MUST override `model_validate()` to accept reference dict and restore from storage
- **FR-006**: System MUST override `model_validate_json()` to accept reference JSON and restore from storage
- **FR-007**: System MUST generate UUID for each model instance on first dump
- **FR-008**: System MUST persist the same UUID across multiple dumps of the same instance
- **FR-009**: System MUST provide PostgreSQL storage backend implementation
- **FR-010**: System MUST provide Redis storage backend implementation
- **FR-011**: System MUST define abstract storage backend interface for custom implementations
- **FR-012**: System MUST validate storage URL format during model class definition
- **FR-013**: System MUST raise descriptive errors for storage connection failures
- **FR-014**: System MUST raise descriptive errors for record not found scenarios
- **FR-015**: System MUST store model data with schema version for future migration support

### Key Entities

- **ExternalBaseModel**: Base class extending Pydantic BaseModel with external storage behavior
- **ExternalConfigDict**: Configuration dictionary for specifying storage backend and options
- **StorageBackend**: Abstract interface defining required methods for storage implementations
- **PostgreSQLBackend**: Concrete implementation for PostgreSQL storage
- **RedisBackend**: Concrete implementation for Redis storage
- **ExternalReference**: Data structure containing class_name and id for serialized references

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Developers can define an external model and store/retrieve data in under 5 lines of code
- **SC-002**: Round-trip serialization (dump + validate) preserves 100% of model field data
- **SC-003**: Storage operation latency adds less than 50ms overhead beyond network round-trip time
- **SC-004**: Library supports models with up to 100 fields without performance degradation
- **SC-005**: Error messages clearly identify the cause and suggest remediation for all failure scenarios
- **SC-006**: Custom backend implementation requires implementing 4 or fewer methods
- **SC-007**: Existing Pydantic model migration requires only changing base class and adding config

## Assumptions

- Users have Python 3.13+ (per project requirements)
- Users provide valid and accessible storage backend connection strings
- Storage backends (PostgreSQL, Redis) are managed externally by the user
- Pydantic v2 is used (for BaseModel and ConfigDict patterns)
- No automatic schema migrations - users handle backend schema management
- Single-threaded usage is the primary use case; thread safety is backend-dependent
