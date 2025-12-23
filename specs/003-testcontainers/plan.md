# Implementation Plan: Testcontainers Integration

**Branch**: `003-testcontainers` | **Date**: 2025-12-23 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-testcontainers/spec.md`

## Summary

Integrate testcontainers-python library to automatically provision isolated PostgreSQL and Redis instances for testing. This enables developers to run all backend tests without manual database installation, ensuring test isolation and reproducible environments across all developer machines.

## Technical Context

**Language/Version**: Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`)  
**Primary Dependencies**: testcontainers[postgres,redis], asyncpg>=0.29.0, redis>=5.0.0, pytest>=8.0.0, pytest-asyncio>=0.23.0  
**Storage**: PostgreSQL (via testcontainers), Redis (via testcontainers)  
**Testing**: pytest with pytest-asyncio (async mode auto)  
**Target Platform**: Developer machines with Docker installed (macOS, Linux, Windows with Docker Desktop)
**Project Type**: Single Python package with test suite  
**Performance Goals**: Container startup within 30 seconds, test overhead ≤10 seconds  
**Constraints**: Docker must be running, offline testing requires pre-cached images  
**Scale/Scope**: Test suite for pydantic-toast library (~4 test files, ~20 tests currently)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Code Quality Standards | ✅ PASS | Type annotations required for all fixtures; explicit dependency injection via fixtures |
| II. Testing Standards | ✅ PASS | Function-based tests only; **no mocks required** - using real containers; module-scoped imports |
| III. User Experience Consistency | ✅ PASS | Clear error messages for Docker not running; predictable fixture behavior |
| IV. Performance Requirements | ✅ PASS | Session-scoped containers minimize startup overhead; documented startup time expectations |

**Gate Status**: ✅ PASS - All principles satisfied. No violations to justify.

### Constitution Alignment Details

**Testing Standards (Critical)**:
- ✅ "No Mocks" principle perfectly aligned - testcontainers provides **real** PostgreSQL/Redis instances
- ✅ Function-based tests preserved - existing tests require no structural changes
- ✅ Module-scoped imports - testcontainers fixtures use standard pytest patterns
- ✅ Meaningful assertions - real database operations provide high-confidence assertions

**Code Quality Standards**:
- ✅ Type Safety - All fixtures will have complete type annotations
- ✅ Explicit Dependencies - Connection URLs explicitly provided via fixtures
- ✅ Error Handling - Container startup failures handled with typed exceptions

## Project Structure

### Documentation (this feature)

```text
specs/003-testcontainers/
├── plan.md              # This file
├── research.md          # Phase 0 output - testcontainers best practices
├── data-model.md        # Phase 1 output - fixture and container entities
├── quickstart.md        # Phase 1 output - how to run tests
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
└── pydantic_toast/      # No changes required to main package
    └── ...

tests/
├── conftest.py          # MODIFY: Add testcontainers fixtures
├── test_base_model.py   # No changes required
├── test_postgresql.py   # MODIFY: Use testcontainers fixtures (remove skipif)
├── test_redis.py        # MODIFY: Use testcontainers fixtures (remove skipif)
└── test_registry.py     # No changes required
```

**Structure Decision**: Single project structure maintained. Changes are isolated to the test directory, specifically `conftest.py` for new fixtures. Existing test files will have minimal modifications (remove `skipif` markers, use new fixtures).

## Complexity Tracking

> No violations detected - table not required.
