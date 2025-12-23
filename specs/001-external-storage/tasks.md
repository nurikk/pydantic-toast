# Tasks: External Storage for Pydantic Models

**Input**: Design documents from `/specs/001-external-storage/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Constitution mandates function-based tests with real backends (no mocks). Tests included.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Project type**: Single Python library with `src/` layout
- **Source**: `src/pydantic_toast/`
- **Tests**: `tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directory structure: `src/pydantic_toast/`, `src/pydantic_toast/backends/`, `tests/`
- [x] T002 Update pyproject.toml with dependencies: pydantic>=2.0.0, optional asyncpg>=0.29.0, redis>=5.0.0
- [x] T003 [P] Configure ruff for linting and formatting in pyproject.toml
- [x] T004 [P] Configure mypy --strict in pyproject.toml
- [x] T005 [P] Configure pytest and pytest-asyncio in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Create exception hierarchy in src/pydantic_toast/exceptions.py (ExternalStorageError, StorageConnectionError, RecordNotFoundError, StorageValidationError)
- [x] T007 Create StorageBackend ABC in src/pydantic_toast/backends/base.py (connect, disconnect, save, load methods)
- [x] T008 Create BackendRegistry in src/pydantic_toast/registry.py (register, create, schemes)
- [x] T009 Create test fixtures in tests/conftest.py (PostgreSQL and Redis test containers or local instances)
- [x] T010 [P] Create src/pydantic_toast/backends/__init__.py with public exports

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Define External Model (Priority: P1) 🎯 MVP

**Goal**: Enable developers to define Pydantic models with ExternalConfigDict that configures storage backend

**Independent Test**: Define an ExternalBaseModel subclass with ExternalConfigDict, instantiate it, verify configuration is accepted

### Tests for User Story 1

- [x] T011 [P] [US1] Test ExternalConfigDict creation with valid storage URL in tests/test_base_model.py
- [x] T012 [P] [US1] Test ExternalConfigDict raises error for invalid URL format in tests/test_base_model.py
- [x] T013 [P] [US1] Test ExternalConfigDict raises error when storage is missing in tests/test_base_model.py

### Implementation for User Story 1

- [x] T014 [US1] Create ExternalConfigDict TypedDict extending ConfigDict in src/pydantic_toast/base.py
- [x] T015 [US1] Create ExternalBaseModel class extending BaseModel in src/pydantic_toast/base.py
- [x] T016 [US1] Implement storage URL validation in ExternalBaseModel.__init_subclass__ in src/pydantic_toast/base.py
- [x] T017 [US1] Add _external_id PrivateAttr for UUID storage in src/pydantic_toast/base.py
- [x] T018 [US1] Create src/pydantic_toast/__init__.py with public API exports (ExternalBaseModel, ExternalConfigDict)

**Checkpoint**: User Story 1 complete - can define external models with storage configuration

---

## Phase 4: User Story 2 - Serialize to External Reference (Priority: P1)

**Goal**: model_dump() returns {"class_name": "...", "id": "..."} and persists data to storage

**Independent Test**: Create instance, call model_dump(), verify reference format and data in storage

### Tests for User Story 2

- [ ] T019 [P] [US2] Test model_dump returns class_name and id format in tests/test_base_model.py
- [ ] T020 [P] [US2] Test model_dump generates UUID on first call in tests/test_base_model.py
- [ ] T021 [P] [US2] Test model_dump returns same id on repeated calls in tests/test_base_model.py
- [ ] T022 [P] [US2] Test model_dump_json returns JSON string of reference in tests/test_base_model.py

### Implementation for User Story 2

- [ ] T023 [US2] Override model_dump() to generate UUID and persist data in src/pydantic_toast/base.py
- [ ] T024 [US2] Override model_dump_json() to return JSON reference in src/pydantic_toast/base.py
- [ ] T025 [US2] Implement _persist_to_storage() async helper in src/pydantic_toast/base.py
- [ ] T026 [US2] Add schema_version, created_at, updated_at to stored data in src/pydantic_toast/base.py

**Checkpoint**: User Story 2 complete - can serialize models to external references

---

## Phase 5: User Story 3 - Restore from External Reference (Priority: P1)

**Goal**: model_validate() accepts reference dict and restores full model from storage

**Independent Test**: Validate JSON reference string, verify returned object has original field values

### Tests for User Story 3

- [ ] T027 [P] [US3] Test model_validate restores full model from reference in tests/test_base_model.py
- [ ] T028 [P] [US3] Test model_validate_json restores from JSON reference in tests/test_base_model.py
- [ ] T029 [P] [US3] Test RecordNotFoundError for nonexistent UUID in tests/test_base_model.py
- [ ] T030 [P] [US3] Test StorageValidationError for class_name mismatch in tests/test_base_model.py

### Implementation for User Story 3

- [ ] T031 [US3] Add model_validator(mode='before') to detect external references in src/pydantic_toast/base.py
- [ ] T032 [US3] Implement _is_external_reference() helper in src/pydantic_toast/base.py
- [ ] T033 [US3] Implement _fetch_from_storage() async helper in src/pydantic_toast/base.py
- [ ] T034 [US3] Add class_name validation during restore in src/pydantic_toast/base.py

**Checkpoint**: User Story 3 complete - full round-trip serialization works

---

## Phase 6: User Story 4 - PostgreSQL Backend (Priority: P2)

**Goal**: Implement PostgreSQLBackend with asyncpg for production database storage

**Independent Test**: Store and retrieve model data with PostgreSQL instance

### Tests for User Story 4

- [ ] T035 [P] [US4] Test PostgreSQLBackend connect creates pool in tests/test_postgresql.py
- [ ] T036 [P] [US4] Test PostgreSQLBackend save stores data in tests/test_postgresql.py
- [ ] T037 [P] [US4] Test PostgreSQLBackend load retrieves data in tests/test_postgresql.py
- [ ] T038 [P] [US4] Test PostgreSQLBackend handles connection errors in tests/test_postgresql.py
- [ ] T039 [P] [US4] Test full round-trip with PostgreSQL backend in tests/test_postgresql.py

### Implementation for User Story 4

- [ ] T040 [US4] Create PostgreSQLBackend class in src/pydantic_toast/backends/postgresql.py
- [ ] T041 [US4] Implement connect() with asyncpg.create_pool() in src/pydantic_toast/backends/postgresql.py
- [ ] T042 [US4] Implement disconnect() to close pool in src/pydantic_toast/backends/postgresql.py
- [ ] T043 [US4] Implement save() with UPSERT query in src/pydantic_toast/backends/postgresql.py
- [ ] T044 [US4] Implement load() with SELECT query in src/pydantic_toast/backends/postgresql.py
- [ ] T045 [US4] Implement ensure_table() to create schema on first connect in src/pydantic_toast/backends/postgresql.py
- [ ] T046 [US4] Register postgresql:// and postgres:// schemes in src/pydantic_toast/backends/__init__.py

**Checkpoint**: User Story 4 complete - PostgreSQL storage backend works

---

## Phase 7: User Story 5 - Redis Backend (Priority: P2)

**Goal**: Implement RedisBackend with redis-py for in-memory storage

**Independent Test**: Store and retrieve model data with Redis instance

### Tests for User Story 5

- [ ] T047 [P] [US5] Test RedisBackend connect creates client in tests/test_redis.py
- [ ] T048 [P] [US5] Test RedisBackend save stores data in tests/test_redis.py
- [ ] T049 [P] [US5] Test RedisBackend load retrieves data in tests/test_redis.py
- [ ] T050 [P] [US5] Test RedisBackend key format is predictable in tests/test_redis.py
- [ ] T051 [P] [US5] Test full round-trip with Redis backend in tests/test_redis.py

### Implementation for User Story 5

- [ ] T052 [US5] Create RedisBackend class in src/pydantic_toast/backends/redis.py
- [ ] T053 [US5] Implement connect() with redis.asyncio.from_url() in src/pydantic_toast/backends/redis.py
- [ ] T054 [US5] Implement disconnect() to close client in src/pydantic_toast/backends/redis.py
- [ ] T055 [US5] Implement save() with JSON serialization in src/pydantic_toast/backends/redis.py
- [ ] T056 [US5] Implement load() with JSON deserialization in src/pydantic_toast/backends/redis.py
- [ ] T057 [US5] Implement _make_key() helper for consistent key format in src/pydantic_toast/backends/redis.py
- [ ] T058 [US5] Register redis:// scheme in src/pydantic_toast/backends/__init__.py

**Checkpoint**: User Story 5 complete - Redis storage backend works

---

## Phase 8: User Story 6 - Custom Storage Backend (Priority: P3)

**Goal**: Enable developers to implement and register custom storage backends

**Independent Test**: Implement a test backend following the interface, register it, use it with an external model

### Tests for User Story 6

- [ ] T059 [P] [US6] Test register_backend adds custom scheme in tests/test_registry.py
- [ ] T060 [P] [US6] Test register_backend rejects non-StorageBackend classes in tests/test_registry.py
- [ ] T061 [P] [US6] Test custom backend works with ExternalBaseModel in tests/test_registry.py
- [ ] T062 [P] [US6] Test unknown scheme raises StorageValidationError in tests/test_registry.py

### Implementation for User Story 6

- [ ] T063 [US6] Add register_backend() function to public API in src/pydantic_toast/__init__.py
- [ ] T064 [US6] Export StorageBackend ABC for subclassing in src/pydantic_toast/__init__.py
- [ ] T065 [US6] Add docstring with custom backend example in src/pydantic_toast/backends/base.py

**Checkpoint**: User Story 6 complete - custom backends can be implemented and registered

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T066 [P] Add py.typed marker file in src/pydantic_toast/py.typed
- [ ] T067 [P] Verify all public APIs have docstrings
- [ ] T068 Run mypy --strict and fix any type errors
- [ ] T069 Run ruff check and fix any lint errors
- [ ] T070 Run ruff format on all source files
- [ ] T071 Run full test suite with pytest
- [ ] T072 Validate quickstart.md examples work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories 1-3 (Phases 3-5)**: Sequential (US2 needs US1, US3 needs US2)
- **User Stories 4-5 (Phases 6-7)**: Can run in parallel after US1-3 complete
- **User Story 6 (Phase 8)**: Can start after Foundational complete
- **Polish (Phase 9)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Define External Model)**: After Foundational - establishes base model
- **US2 (Serialize)**: After US1 - needs ExternalBaseModel to override model_dump
- **US3 (Restore)**: After US2 - needs serialization to test restore
- **US4 (PostgreSQL)**: After US3 - needs full round-trip to test backend
- **US5 (Redis)**: After US3 - needs full round-trip to test backend (parallel with US4)
- **US6 (Custom Backend)**: After Foundational - only needs registry and ABC

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Implementation tasks depend on prior tasks in the story
- Story complete before moving to dependent stories

### Parallel Opportunities

- T003, T004, T005 (Setup config) can run in parallel
- T011, T012, T013 (US1 tests) can run in parallel
- T019, T020, T021, T022 (US2 tests) can run in parallel
- T027, T028, T029, T030 (US3 tests) can run in parallel
- T035-T039 (US4 tests) can run in parallel
- T047-T051 (US5 tests) can run in parallel
- T059-T062 (US6 tests) can run in parallel
- US4 and US5 (backend implementations) can run in parallel after US3

---

## Parallel Example: User Story 4

```bash
# Launch all tests for User Story 4 together:
Task: "Test PostgreSQLBackend connect creates pool in tests/test_postgresql.py"
Task: "Test PostgreSQLBackend save stores data in tests/test_postgresql.py"
Task: "Test PostgreSQLBackend load retrieves data in tests/test_postgresql.py"
Task: "Test PostgreSQLBackend handles connection errors in tests/test_postgresql.py"
Task: "Test full round-trip with PostgreSQL backend in tests/test_postgresql.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1-3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phases 3-5: User Stories 1, 2, 3 (define, serialize, restore)
4. **STOP and VALIDATE**: Full round-trip works with any registered backend
5. Library is usable with custom backends at this point

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Complete US1 → Can define models with storage config
3. Complete US2 → Can serialize to external references
4. Complete US3 → Full round-trip works (MVP!)
5. Complete US4 → PostgreSQL backend available
6. Complete US5 → Redis backend available
7. Complete US6 → Custom backends documented and easy to implement

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once US3 is done:
   - Developer A: User Story 4 (PostgreSQL)
   - Developer B: User Story 5 (Redis)
3. US6 can start after Foundational, independent of US4/US5

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Constitution requires: function-based tests, no mocks, real backends
- Each user story should be independently testable
- Verify tests fail before implementing
- Commit after each task or logical group
