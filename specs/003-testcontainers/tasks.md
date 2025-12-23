# Tasks: Testcontainers Integration

**Input**: Design documents from `/specs/003-testcontainers/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add testcontainers dependency and configure project

- [x] T001 Add testcontainers[postgres,redis]>=4.0.0 to dev dependencies in pyproject.toml
- [x] T002 Run uv sync to install new dependencies

---

## Phase 2: Foundational (Docker Check Fixture)

**Purpose**: Shared infrastructure that enables all user stories

- [x] T003 Add Docker availability check fixture (session-scoped, autouse) in tests/conftest.py

**Checkpoint**: Foundation ready - user story implementation can begin

---

## Phase 3: User Story 1 - Isolated PostgreSQL Testing (Priority: P1) 🎯 MVP

**Goal**: Run PostgreSQL tests without manual database setup using testcontainers

**Independent Test**: Run `pytest tests/test_postgresql.py` without POSTGRES_URL env var - all tests should pass

### Implementation for User Story 1

- [x] T004 [US1] Add PostgresContainer session-scoped fixture (with env var override) in tests/conftest.py
- [x] T005 [US1] Add postgres_url fixture that returns URL from container or env var in tests/conftest.py
- [x] T006 [US1] Remove pytestmark skipif and local postgres_url fixture in tests/test_postgresql.py
- [x] T007 [US1] Update postgres_backend fixture to use conftest postgres_url in tests/test_postgresql.py

**Checkpoint**: PostgreSQL tests run without manual database setup

---

## Phase 4: User Story 2 - Isolated Redis Testing (Priority: P2)

**Goal**: Run Redis tests without manual Redis server setup using testcontainers

**Independent Test**: Run `pytest tests/test_redis.py` without REDIS_URL env var - all tests should pass

### Implementation for User Story 2

- [x] T008 [US2] Add RedisContainer session-scoped fixture (with env var override) in tests/conftest.py
- [x] T009 [US2] Add redis_url fixture that returns URL from container or env var in tests/conftest.py
- [x] T010 [US2] Remove pytestmark skipif and local redis_url fixture in tests/test_redis.py
- [x] T011 [US2] Update redis_backend fixture to use conftest redis_url in tests/test_redis.py

**Checkpoint**: Redis tests run without manual Redis server setup

---

## Phase 5: User Story 3 - Parallel Test Execution (Priority: P3)

**Goal**: Tests can run in parallel without port conflicts

**Independent Test**: Run `pytest -n auto` (with pytest-xdist) - tests should pass without conflicts

### Implementation for User Story 3

- [x] T012 [US3] Verify session-scoped containers work with pytest-xdist (containers per worker)
- [x] T013 [US3] Document parallel execution in quickstart.md if not already covered

**Checkpoint**: All user stories complete - tests run in parallel without conflicts

---

## Phase 6: Polish

**Purpose**: Validation and cleanup

- [x] T014 Run full test suite without any env vars set: pytest
- [x] T015 Run mypy type check on tests/conftest.py
- [x] T016 Verify quickstart.md instructions work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1
- **User Story 1 (Phase 3)**: Depends on Phase 2
- **User Story 2 (Phase 4)**: Depends on Phase 2 (can run parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Phase 3 and Phase 4
- **Polish (Phase 6)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Independent after Foundational
- **User Story 2 (P2)**: Independent after Foundational (can run parallel with US1)
- **User Story 3 (P3)**: Requires US1 and US2 complete (needs both containers working)

---

## Parallel Example: User Stories 1 and 2

```bash
# After Foundational phase, these can run in parallel:
# Worker A: User Story 1 (PostgreSQL)
Task: T004, T005, T006, T007

# Worker B: User Story 2 (Redis)  
Task: T008, T009, T010, T011
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: User Story 1 (T004-T007)
4. **VALIDATE**: `pytest tests/test_postgresql.py` passes without env vars
5. MVP complete - PostgreSQL tests work without manual setup

### Full Implementation

1. Setup + Foundational → T001-T003
2. User Story 1 → T004-T007 → Validate PostgreSQL tests
3. User Story 2 → T008-T011 → Validate Redis tests
4. User Story 3 → T012-T013 → Validate parallel execution
5. Polish → T014-T016 → Full validation

---

## Notes

- All fixture changes are in tests/conftest.py
- Test file changes are minimal (remove skipif, remove local fixtures)
- Session-scoped containers minimize startup overhead
- Env var override preserved for debugging (FR-012)
