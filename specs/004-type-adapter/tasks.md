# Tasks: External TypeAdapter

**Input**: Design documents from `/specs/004-type-adapter/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Not explicitly requested in feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/pydantic_toast/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and new module structure

- [X] T001 Create new module file src/pydantic_toast/type_adapter.py with module docstring and imports
- [X] T002 Add ExternalTypeAdapter to public exports in src/pydantic_toast/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Helper functions that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Implement `_get_type_name()` helper function in src/pydantic_toast/type_adapter.py for generating canonical type identifiers
- [X] T004 Implement `ExternalTypeAdapter.__init__()` with URL validation and TypeAdapter creation in src/pydantic_toast/type_adapter.py
- [X] T005 Implement `type_name` property in src/pydantic_toast/type_adapter.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Store Arbitrary Types Externally (Priority: P1)

**Goal**: Enable storing TypedDict, dataclasses, and other arbitrary types in external storage without requiring inheritance from ExternalBaseModel

**Independent Test**: Create an `ExternalTypeAdapter` for a `TypedDict`, save it, and load it back - delivers immediate value for users with existing type definitions

### Implementation for User Story 1

- [X] T006 [US1] Implement `save_external()` async method in src/pydantic_toast/type_adapter.py - validate data, generate UUID, serialize with TypeAdapter, store via backend
- [X] T007 [US1] Implement `load_external()` async method in src/pydantic_toast/type_adapter.py - verify type name match, load from backend, validate and reconstruct type

**Checkpoint**: At this point, User Story 1 should be fully functional - async save/load of TypedDicts and dataclasses works

---

## Phase 4: User Story 2 - Store Collections of Models (Priority: P2)

**Goal**: Store typed collections (list[Model], dict[str, Model]) as single external references

**Independent Test**: Create an `ExternalTypeAdapter` for `list[SomeModel]`, save a list of models, and load them back as a validated list

### Implementation for User Story 2

- [X] T008 [US2] Verify collection type support in src/pydantic_toast/type_adapter.py - ensure `_get_type_name()` handles nested generics like `list[User]`, `dict[str, Product]`
- [X] T009 [US2] Verify TypeAdapter serialization handles collections correctly - `dump_python(mode="json")` for nested Pydantic models

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - collections of models can be stored and retrieved

---

## Phase 5: User Story 3 - Synchronous API Access (Priority: P3)

**Goal**: Provide sync wrappers for codebases that don't use async/await

**Independent Test**: Call `save_external_sync()` and `load_external_sync()` methods outside of any async context

### Implementation for User Story 3

- [X] T010 [P] [US3] Implement `save_external_sync()` method in src/pydantic_toast/type_adapter.py using `_run_sync()` from base.py
- [X] T011 [P] [US3] Implement `load_external_sync()` method in src/pydantic_toast/type_adapter.py using `_run_sync()` from base.py

**Checkpoint**: All user stories should now be independently functional - async and sync APIs complete

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T012 [P] Add comprehensive docstrings with examples to all public methods in src/pydantic_toast/type_adapter.py per contract specification
- [X] T013 Run quickstart.md validation - verify all code examples work correctly
- [X] T014 Run `just check` to verify format, typecheck, and tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 -> P2 -> P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 methods existing (uses same save/load)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 methods existing (wraps async methods)

### Within Each User Story

- Core implementation before advanced features
- Story complete before moving to next priority
- Commit after each task or logical group

### Parallel Opportunities

- T010 and T011 (sync methods) can run in parallel - different methods, same pattern
- T012 (docstrings) can run in parallel with validation tasks
- Once Foundational phase completes, US2 and US3 can start in parallel if US1 methods exist

---

## Parallel Example: User Story 3

```bash
# Launch sync methods in parallel:
Task: "Implement save_external_sync() method in src/pydantic_toast/type_adapter.py"
Task: "Implement load_external_sync() method in src/pydantic_toast/type_adapter.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (save/load arbitrary types)
4. **STOP and VALIDATE**: Test with TypedDict and dataclass examples
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Story 1 -> Test independently -> Deploy/Demo (MVP!)
3. Add User Story 2 -> Test collections -> Deploy/Demo
4. Add User Story 3 -> Test sync API -> Deploy/Demo
5. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files/methods, no dependencies
- [Story] label maps task to specific user story for traceability
- Contract file at specs/004-type-adapter/contracts/storage_backend.py contains full implementation specification
- Reuse existing `_run_sync()` from base.py - no code duplication
- No new dependencies required - pydantic TypeAdapter is already available
- No database schema changes - uses existing backend storage format
