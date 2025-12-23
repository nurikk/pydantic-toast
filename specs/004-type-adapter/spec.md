# Feature Specification: External TypeAdapter

**Feature Branch**: `004-type-adapter`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "Implement functionality similar to pydantic TypeAdapter"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Store Arbitrary Types Externally (Priority: P1)

As a developer, I want to store arbitrary Python types (dataclasses, TypedDicts, lists, dictionaries) in external storage without requiring them to inherit from `ExternalBaseModel`, so that I can use pydantic-toast with existing types that I cannot modify.

**Why this priority**: This is the core value proposition of the feature. Many users have existing types (dataclasses from other libraries, TypedDicts, nested collections) that they cannot modify to inherit from `ExternalBaseModel`. Without this capability, pydantic-toast is limited to models the user fully controls.

**Independent Test**: Can be fully tested by creating an `ExternalTypeAdapter` for a `TypedDict`, saving it, and loading it back - delivers immediate value for users with existing type definitions.

**Acceptance Scenarios**:

1. **Given** a TypedDict definition and an `ExternalTypeAdapter` configured with a storage URL, **When** I call `save_external(data)` with valid data matching the type, **Then** the data is persisted and I receive an `ExternalReference` containing the type name and a unique identifier.

2. **Given** a valid `ExternalReference` from a previous save operation, **When** I call `load_external(reference)`, **Then** the original data is retrieved and validated against the type definition.

3. **Given** a dataclass (not inheriting from ExternalBaseModel), **When** I create an `ExternalTypeAdapter` for it and save an instance, **Then** the data is stored and can be loaded back as a valid dataclass instance.

---

### User Story 2 - Store Collections of Models (Priority: P2)

As a developer, I want to store collections of Pydantic models (like `list[User]` or `dict[str, Product]`) as a single external reference, so that I can efficiently store and retrieve batches of related models.

**Why this priority**: This extends the P1 capability to typed collections, which is a common use case when dealing with API responses or batch operations. It builds on the core functionality.

**Independent Test**: Can be fully tested by creating an `ExternalTypeAdapter` for `list[SomeModel]`, saving a list of models, and loading them back as a validated list.

**Acceptance Scenarios**:

1. **Given** an `ExternalTypeAdapter` configured for `list[Item]` where Item is a Pydantic model, **When** I save a list containing multiple Item instances, **Then** all items are stored together and retrieved as a single operation.

2. **Given** an `ExternalTypeAdapter` configured for `dict[str, Product]`, **When** I save a dictionary mapping IDs to Product models, **Then** the entire dictionary is stored and can be loaded back with all keys and values preserved.

---

### User Story 3 - Synchronous API Access (Priority: P3)

As a developer working in synchronous codebases, I want synchronous versions of save and load operations, so that I can use pydantic-toast without async/await.

**Why this priority**: Mirrors the existing sync API pattern in `ExternalBaseModel`. Important for adoption but builds on async-first implementation.

**Independent Test**: Can be fully tested by calling `save_external_sync()` and `load_external_sync()` methods outside of any async context.

**Acceptance Scenarios**:

1. **Given** an `ExternalTypeAdapter` and valid data, **When** I call `save_external_sync(data)` from a synchronous context, **Then** the data is saved and an `ExternalReference` is returned without requiring async/await.

2. **Given** a valid `ExternalReference`, **When** I call `load_external_sync(reference)` from a synchronous context, **Then** the data is loaded and returned without requiring async/await.

---

### Edge Cases

- What happens when data doesn't match the type? Validation should fail with a clear `StorageValidationError` before attempting storage.
- What happens when loading with a mismatched type adapter (different type than was used to save)? Should fail with `StorageValidationError` indicating type mismatch.
- What happens when the stored data has been manually modified and no longer validates? Should fail with a validation error during load.
- How does the system handle primitive types like `int` or `str`? Should support any type Pydantic's TypeAdapter supports.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide an `ExternalTypeAdapter` class that accepts any type supported by Pydantic's `TypeAdapter`
- **FR-002**: System MUST validate data against the specified type before saving to external storage
- **FR-003**: System MUST validate data against the specified type when loading from external storage
- **FR-004**: `ExternalTypeAdapter` MUST support both async (`save_external`, `load_external`) and sync (`save_external_sync`, `load_external_sync`) operations
- **FR-005**: System MUST return an `ExternalReference` containing a type identifier and unique ID when saving data
- **FR-006**: System MUST raise `StorageValidationError` when data fails type validation (before save or after load)
- **FR-007**: System MUST raise `RecordNotFoundError` when loading a reference that doesn't exist
- **FR-008**: System MUST work with all existing storage backends (PostgreSQL, Redis, S3)
- **FR-009**: System MUST support collection types like `list[T]`, `dict[K, V]`, `set[T]`
- **FR-010**: System MUST store a type identifier to detect type mismatches during load
- **FR-011**: System MUST support TypedDict, dataclasses, NamedTuple, and other types Pydantic supports

### Key Entities

- **ExternalTypeAdapter**: A wrapper around a type definition that provides external storage capabilities. Accepts a type parameter and a storage URL. Maintains a Pydantic TypeAdapter internally for validation.
- **ExternalReference**: Same TypedDict as used by `ExternalBaseModel` - contains `class_name` (type identifier) and `id` (unique identifier). Enables consistent reference format across the library.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can save and load any type supported by Pydantic's TypeAdapter within the expected storage backend latency
- **SC-002**: Type validation errors are detected and reported with clear error messages before any storage operation is attempted
- **SC-003**: API consistency with existing `ExternalBaseModel` methods - same method naming pattern, same exception types, same reference format
- **SC-004**: 100% of existing storage backends work with `ExternalTypeAdapter` without backend modifications
- **SC-005**: Users can migrate from inline data to external storage without changing their type definitions

## Assumptions

- The type identifier stored in the external reference will use Python's type representation (e.g., `"list[User]"`, `"dict[str, Product]"`) to enable type mismatch detection
- The storage format will match `ExternalBaseModel` (same schema_version, created_at, updated_at metadata) to maintain consistency
- Connection pooling and connection management will mirror `ExternalBaseModel` behavior (connect on each operation, disconnect after)
