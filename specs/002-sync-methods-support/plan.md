# Implementation Plan: Synchronous Methods Support

**Branch**: `002-sync-methods-support` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-sync-methods-support/spec.md`

## Summary

Add first-class support for synchronous methods to achieve 100% pydantic API compatibility. The current implementation overrides pydantic's standard methods (`model_dump`, `model_validate`, etc.) with async versions, breaking compatibility with code expecting synchronous pydantic behavior. This plan introduces dedicated storage methods while preserving pydantic's native sync API.

## Technical Context

**Language/Version**: Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`)
**Primary Dependencies**: pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis)
**Storage**: PostgreSQL (JSONB), Redis (JSON strings)
**Testing**: pytest>=8.0.0, pytest-asyncio>=0.23.0
**Target Platform**: Python library (cross-platform)
**Project Type**: Single library project
**Performance Goals**: Storage operations should add minimal overhead; sync wrappers should not introduce unnecessary blocking
**Constraints**: Must maintain backward compatibility with existing StorageBackend interface; sync operations may block in sync contexts
**Scale/Scope**: Library feature - affects ExternalBaseModel API surface

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Code Quality Standards** | | |
| Type Safety | ✅ PASS | All new methods will have complete type annotations |
| Single Responsibility | ✅ PASS | Clear separation: pydantic methods (sync) vs storage methods (async) |
| Explicit Over Implicit | ✅ PASS | No magic - dedicated methods for storage, pydantic methods unchanged |
| No Dead Code | ✅ PASS | Removing async overrides of pydantic methods |
| Consistent Naming | ✅ PASS | New methods follow `save_external`/`load_external` naming pattern |
| Error Handling | ✅ PASS | Storage errors wrapped in typed exceptions |
| **II. Testing Standards** | | |
| Function-Based Tests Only | ✅ PASS | All tests are function-based per existing pattern |
| No Mocks | ✅ PASS | Using real storage backends via fixtures |
| Module-Scoped Imports | ✅ PASS | No function-scoped imports |
| Meaningful Assertions | ✅ PASS | Tests verify specific behavior |
| Test Naming | ✅ PASS | Following `test_<behavior>_<condition>_<expected>` |
| Coverage Requirements | ✅ PASS | Both sync and async paths tested |
| **III. User Experience Consistency** | | |
| Consistent Error Messages | ✅ PASS | Same error types for sync and async operations |
| Predictable Behavior | ✅ PASS | Pydantic methods behave exactly like pydantic.BaseModel |
| Progressive Disclosure | ✅ PASS | Simple use (pydantic API) remains simple; storage is opt-in |
| Clear Documentation | ✅ PASS | Docstrings distinguish pydantic vs storage methods |
| Graceful Degradation | ✅ PASS | Sync wrappers handle event loop detection |
| **IV. Performance Requirements** | | |
| Baseline Metrics | ✅ PASS | Sync wrappers add minimal overhead (single asyncio.run call) |
| No Premature Optimization | ✅ PASS | Simple implementation first |
| Resource Awareness | ✅ PASS | Connection management unchanged |
| Async by Default | ✅ PASS | Storage operations remain async; sync wrappers provided |
| Startup Time | ✅ PASS | No impact on startup |
| Regression Prevention | ✅ PASS | Existing tests continue to validate behavior |

**Gate Result**: ✅ PASS - No violations

## Project Structure

### Documentation (this feature)

```text
specs/002-sync-methods-support/
├── plan.md              # This file
├── research.md          # Phase 0 output - design decisions
├── data-model.md        # Phase 1 output - entity definitions
├── quickstart.md        # Phase 1 output - usage examples
├── contracts/           # Phase 1 output - API contracts
│   └── storage_backend.py
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
src/pydantic_toast/
├── __init__.py          # Public exports (update for new methods)
├── base.py              # ExternalBaseModel (PRIMARY CHANGE)
├── exceptions.py        # Exception types (unchanged)
├── registry.py          # Backend registry (unchanged)
└── backends/
    ├── __init__.py      # Backend exports (unchanged)
    ├── base.py          # StorageBackend interface (unchanged)
    ├── postgresql.py    # PostgreSQL backend (unchanged)
    └── redis.py         # Redis backend (unchanged)

tests/
├── conftest.py          # Test fixtures (unchanged)
├── test_base_model.py   # ExternalBaseModel tests (UPDATE)
├── test_postgresql.py   # PostgreSQL tests (unchanged)
├── test_redis.py        # Redis tests (unchanged)
└── test_registry.py     # Registry tests (unchanged)
```

**Structure Decision**: Single library project. Changes isolated to `base.py` (ExternalBaseModel) and corresponding tests. Backend implementations remain unchanged.

## Complexity Tracking

No violations requiring justification.
