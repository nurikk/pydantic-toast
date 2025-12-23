# Implementation Plan: External Storage for Pydantic Models

**Branch**: `001-external-storage` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-external-storage/spec.md`

## Summary

Build a Python library (`pydantic-toast`) that extends Pydantic BaseModel to automatically store model data in external storage backends (PostgreSQL, Redis). When dumping a model, it returns a lightweight reference (`{"class_name": "...", "id": "..."}`) while persisting actual data externally. Validation restores the full model from storage. Uses asyncpg for PostgreSQL, redis-py for Redis, and provides an extensible backend interface.

## Technical Context

**Language/Version**: Python 3.13+  
**Primary Dependencies**: pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis)  
**Storage**: PostgreSQL (JSONB), Redis (JSON strings)  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Python library (cross-platform)  
**Project Type**: single (Python library)  
**Performance Goals**: <50ms overhead beyond network round-trip (SC-003)  
**Constraints**: Async-first design, minimal API surface  
**Scale/Scope**: Models with up to 100 fields (SC-004)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Code Quality Standards | ✅ PASS | Type annotations required, explicit error handling planned |
| II. Testing Standards | ✅ PASS | Function-based tests, no mocks (use real backends via fixtures) |
| III. User Experience Consistency | ✅ PASS | Consistent error messages, predictable API |
| IV. Performance Requirements | ✅ PASS | Performance metrics documented in research.md |

**Quality Gates**:
- Type Check: mypy --strict
- Lint: ruff
- Format: ruff format
- Tests: pytest with real storage backends

## Project Structure

### Documentation (this feature)

```text
specs/001-external-storage/
├── plan.md              # This file
├── research.md          # Technology decisions and rationale
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Usage examples and integration guide
├── contracts/           # Interface definitions
│   └── storage_backend.py
└── tasks.md             # Implementation tasks (Phase 2)
```

### Source Code (repository root)

```text
src/
└── pydantic_toast/
    ├── __init__.py          # Public API exports
    ├── base.py              # ExternalBaseModel, ExternalConfigDict
    ├── backends/
    │   ├── __init__.py
    │   ├── base.py          # StorageBackend ABC
    │   ├── postgresql.py    # PostgreSQLBackend
    │   └── redis.py         # RedisBackend
    ├── exceptions.py        # Custom exception hierarchy
    └── registry.py          # Backend registration

tests/
├── conftest.py              # Fixtures for PostgreSQL/Redis
├── test_base_model.py       # ExternalBaseModel tests
├── test_postgresql.py       # PostgreSQL backend tests
├── test_redis.py            # Redis backend tests
└── test_registry.py         # Backend registration tests
```

**Structure Decision**: Single Python library project with `src/` layout for proper packaging. Test fixtures will use real PostgreSQL and Redis instances (testcontainers or local).

## Complexity Tracking

No constitution violations requiring justification.

## Phase Artifacts

| Phase | Artifact | Status |
|-------|----------|--------|
| Phase 0 | research.md | ✅ Complete |
| Phase 1 | data-model.md | ✅ Complete |
| Phase 1 | contracts/storage_backend.py | ✅ Complete |
| Phase 1 | quickstart.md | ✅ Complete |
| Phase 2 | tasks.md | Pending (/speckit.tasks) |
