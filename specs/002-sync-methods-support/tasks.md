# Tasks: Synchronous Methods Support

**Input**: Design documents from `/specs/002-sync-methods-support/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are included based on constitution requirements (Testing Standards mandate coverage).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/pydantic_toast/`, `tests/` at repository root

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare codebase for the API change

- [X] T001 Review existing async method overrides in src/pydantic_toast/base.py
- [X] T002 [P] Create backup of current test expectations in tests/test_base_model.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utility functions that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Add `_run_sync` helper function for event loop detection in src/pydantic_toast/base.py
- [X] T004 Add `is_external_reference` static method to ExternalBaseModel in src/pydantic_toast/base.py
- [X] T005 [P] Add ExternalReference TypedDict to src/pydantic_toast/base.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Standard Pydantic API Usage (Priority: P1) 🎯 MVP

**Goal**: Preserve standard pydantic methods (model_dump, model_dump_json, model_validate, model_validate_json) to work synchronously without await

**Independent Test**: Create an ExternalBaseModel subclass and verify all pydantic methods work synchronously, returning model data (not external references)

### Tests for User Story 1

- [X] T006 [P] [US1] Add test_model_dump_returns_dict_synchronously in tests/test_base_model.py
- [X] T007 [P] [US1] Add test_model_dump_json_returns_json_string_synchronously in tests/test_base_model.py
- [X] T008 [P] [US1] Add test_model_validate_creates_instance_synchronously in tests/test_base_model.py
- [X] T009 [P] [US1] Add test_model_validate_json_creates_instance_synchronously in tests/test_base_model.py

### Implementation for User Story 1

- [X] T010 [US1] Remove async override of model_dump method in src/pydantic_toast/base.py
- [X] T011 [US1] Remove async override of model_dump_json method in src/pydantic_toast/base.py
- [X] T012 [US1] Remove async override of model_validate classmethod in src/pydantic_toast/base.py
- [X] T013 [US1] Remove async override of model_validate_json classmethod in src/pydantic_toast/base.py
- [X] T014 [US1] Verify pydantic methods are inherited correctly (no type: ignore needed)

**Checkpoint**: At this point, all pydantic methods work synchronously - core pydantic compatibility achieved

---

## Phase 4: User Story 2 - External Storage Operations (Priority: P2)

**Goal**: Provide dedicated async methods for storage persistence (save_external, load_external) that return external references

**Independent Test**: Create an ExternalBaseModel, persist using save_external(), restore using load_external(), verify field values match

### Tests for User Story 2

- [X] T015 [P] [US2] Add test_save_external_persists_and_returns_reference in tests/test_base_model.py
- [X] T016 [P] [US2] Add test_load_external_restores_model_from_reference in tests/test_base_model.py
- [X] T017 [P] [US2] Add test_save_load_external_roundtrip_preserves_data in tests/test_base_model.py
- [X] T018 [P] [US2] Add test_load_external_raises_not_found_for_invalid_id in tests/test_base_model.py
- [X] T019 [P] [US2] Add test_load_external_raises_validation_error_for_class_mismatch in tests/test_base_model.py

### Implementation for User Story 2

- [X] T020 [US2] Implement async save_external method in src/pydantic_toast/base.py (move logic from old model_dump)
- [X] T021 [US2] Implement async load_external classmethod in src/pydantic_toast/base.py (move logic from old model_validate)
- [X] T022 [US2] Add docstrings with examples to save_external and load_external
- [X] T023 [US2] Update src/pydantic_toast/__init__.py to export new method names in __all__

**Checkpoint**: At this point, async storage operations work correctly with dedicated methods

---

## Phase 5: User Story 3 - Mixed Sync/Async Usage (Priority: P3)

**Goal**: Provide sync wrappers (save_external_sync, load_external_sync) for non-async contexts with proper event loop detection

**Independent Test**: Perform storage operations using sync wrappers in a non-async context, verify same behavior as async versions

### Tests for User Story 3

- [X] T024 [P] [US3] Add test_save_external_sync_works_in_sync_context in tests/test_base_model.py
- [X] T025 [P] [US3] Add test_load_external_sync_works_in_sync_context in tests/test_base_model.py
- [X] T026 [P] [US3] Add test_save_external_sync_raises_error_in_async_context in tests/test_base_model.py
- [X] T027 [P] [US3] Add test_load_external_sync_raises_error_in_async_context in tests/test_base_model.py

### Implementation for User Story 3

- [X] T028 [US3] Implement save_external_sync method using _run_sync helper in src/pydantic_toast/base.py
- [X] T029 [US3] Implement load_external_sync classmethod using _run_sync helper in src/pydantic_toast/base.py
- [X] T030 [US3] Add RuntimeError with helpful message for async context detection
- [X] T031 [US3] Add docstrings with examples to sync wrapper methods

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, documentation, and validation

- [X] T032 Update existing tests to use new API (replace await model.model_dump() with await model.save_external())
- [X] T033 [P] Remove any dead code from old async overrides in src/pydantic_toast/base.py
- [X] T034 [P] Run mypy --strict to verify type annotations in src/pydantic_toast/base.py
- [X] T035 [P] Run ruff check and ruff format on modified files
- [X] T036 Run full test suite with pytest to verify no regressions
- [X] T037 Validate quickstart.md examples work correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories should proceed sequentially (P1 → P2 → P3) as each builds on previous
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - Removes async overrides first
- **User Story 2 (P2)**: Depends on US1 - Implements new async methods using logic from removed overrides
- **User Story 3 (P3)**: Depends on US2 - Wraps async methods with sync wrappers

### Within Each User Story

- Tests SHOULD be written first to verify expected behavior
- Implementation follows test creation
- Story complete before moving to next priority

### Parallel Opportunities

- All Foundational tasks marked [P] can run in parallel (T004, T005)
- All tests for a user story marked [P] can run in parallel
- Polish tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 Tests

```bash
# Launch all tests for User Story 1 together:
Task: "Add test_model_dump_returns_dict_synchronously in tests/test_base_model.py"
Task: "Add test_model_dump_json_returns_json_string_synchronously in tests/test_base_model.py"
Task: "Add test_model_validate_creates_instance_synchronously in tests/test_base_model.py"
Task: "Add test_model_validate_json_creates_instance_synchronously in tests/test_base_model.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test pydantic compatibility independently
5. Commit - this is already valuable (pydantic API works!)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test → Commit (pydantic methods work sync!)
3. Add User Story 2 → Test → Commit (async storage methods available!)
4. Add User Story 3 → Test → Commit (sync wrappers for non-async contexts!)
5. Each story adds value without breaking previous stories

### Migration Note

This is a **BREAKING CHANGE**. After implementation:

| Old Code | New Code |
|----------|----------|
| `await model.model_dump()` | `await model.save_external()` |
| `await Model.model_validate(ref)` | `await Model.load_external(ref)` |
| `model.model_dump()` (failed before) | `model.model_dump()` ✅ Works now! |

---

## Notes

- [P] tasks = different files or independent code paths, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each phase completion
- This feature is a breaking change - update changelog
