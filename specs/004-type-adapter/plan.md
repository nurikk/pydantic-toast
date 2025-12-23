# Implementation Plan: External TypeAdapter

**Branch**: `004-type-adapter` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-type-adapter/spec.md`

## Summary

Implement `ExternalTypeAdapter` class that wraps Pydantic's `TypeAdapter` to enable external storage of arbitrary Python types (TypedDict, dataclasses, NamedTuple, collections) without requiring inheritance from `ExternalBaseModel`. Provides async/sync save and load operations with full type validation, returning consistent `ExternalReference` format.

## Technical Context

**Language/Version**: Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`)
**Primary Dependencies**: pydantic>=2.0.0 (TypeAdapter), asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis), aiobotocore>=3.0.0 (S3)
**Storage**: PostgreSQL (JSONB), Redis (JSON strings), S3 (JSON objects) - via existing backends
**Testing**: pytest>=8.0.0, pytest-asyncio>=0.23.0, testcontainers[postgres,redis,localstack]>=4.0.0
**Target Platform**: Linux server / cross-platform Python library
**Project Type**: single (Python library)
**Performance Goals**: Same latency as ExternalBaseModel (backend-dependent: ~1-10ms for PostgreSQL/Redis, ~50-100ms for S3)
**Constraints**: Must work with existing StorageBackend interface without modification
**Scale/Scope**: Library for storing arbitrary types; typical usage: individual objects or small collections

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Code Quality Standards | ✅ PASS | Complete type annotations required for all new code; single-purpose `ExternalTypeAdapter` class; explicit storage URL injection; no dead code; snake_case naming |
| II. Testing Standards | ✅ PASS | Function-based tests only; no mocks (use InMemoryBackend fixture); module-scoped imports; descriptive test names |
| III. User Experience Consistency | ✅ PASS | Same method naming as `ExternalBaseModel` (`save_external`, `load_external`, `*_sync` variants); same exceptions (`StorageValidationError`, `RecordNotFoundError`); same `ExternalReference` return type |
| IV. Performance Requirements | ✅ PASS | Async by default with sync wrappers; same I/O patterns as existing code; no additional overhead beyond TypeAdapter validation |

**Gate Result**: ✅ All principles satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-type-adapter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/pydantic_toast/
├── __init__.py          # Add ExternalTypeAdapter export
├── base.py              # Existing ExternalBaseModel (unchanged)
├── type_adapter.py      # NEW: ExternalTypeAdapter implementation
├── exceptions.py        # Existing exceptions (unchanged)
├── registry.py          # Existing registry (unchanged)
└── backends/            # Existing backends (unchanged)

tests/
├── conftest.py          # Existing fixtures (unchanged)
├── test_base_model.py   # Existing tests (unchanged)
├── test_type_adapter.py # NEW: ExternalTypeAdapter tests
└── test_*.py            # Existing backend tests (unchanged)
```

**Structure Decision**: Single new module `type_adapter.py` for `ExternalTypeAdapter` class. No changes to existing modules except `__init__.py` exports. Follows existing project structure pattern.

## Complexity Tracking

> No constitution violations requiring justification.

## Post-Design Constitution Re-Check

*GATE: Verified after Phase 1 design completion.*

| Principle | Status | Post-Design Evidence |
|-----------|--------|---------------------|
| I. Code Quality Standards | ✅ PASS | Contract shows complete type annotations (`Generic[T]`, `TypeVar`, return types); single-purpose class; explicit `storage_url` injection in constructor; no unused code; `_get_type_name` helper function under 15 lines |
| II. Testing Standards | ✅ PASS | Tests will use existing `InMemoryBackend` fixture; function-based tests per AGENTS.md; module-level imports only |
| III. User Experience Consistency | ✅ PASS | Contract uses identical method names (`save_external`, `load_external`, `*_sync`); same exception types; same `ExternalReference` TypedDict; clear docstrings with examples |
| IV. Performance Requirements | ✅ PASS | Async-first design with `_run_sync` for sync wrappers; no blocking calls in async context; TypeAdapter reused (not recreated per call); connect/disconnect pattern matches existing backends |

**Post-Design Gate Result**: ✅ All principles satisfied. Ready for Phase 2 task breakdown.
