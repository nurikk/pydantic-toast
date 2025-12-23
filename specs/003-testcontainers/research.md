# Research: Testcontainers Integration

**Feature**: 003-testcontainers  
**Date**: 2025-12-23  
**Status**: Complete

## Research Questions

### R1: How to integrate testcontainers-python with pytest-asyncio?

**Decision**: Use synchronous container management with async test functions.

**Rationale**: testcontainers-python container lifecycle (`start()`, `stop()`) is synchronous. The async database operations (via asyncpg, redis) happen inside test functions after container is ready. This matches the existing test patterns in the codebase.

**Alternatives Considered**:
- Full async container management: Not supported by testcontainers-python
- Wrapping in `asyncio.to_thread()`: Unnecessary complexity, container ops are I/O-wait not CPU-bound

**Implementation Pattern**:
```python
@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    container = PostgresContainer("postgres:16")
    container.start()
    yield container
    container.stop()

@pytest.fixture
async def postgres_backend(postgres_container: PostgresContainer) -> AsyncGenerator[PostgreSQLBackend, None]:
    url = postgres_container.get_connection_url()
    backend = PostgreSQLBackend(url.replace("psycopg2", "postgresql"))
    await backend.connect()
    yield backend
    await backend.disconnect()
```

---

### R2: What fixture scope to use for containers?

**Decision**: Session-scoped containers with function-scoped database state.

**Rationale**:
- Session scope minimizes container startup overhead (30+ seconds per container)
- Function scope for actual backends ensures test isolation
- Database cleanup between tests via table truncation or fresh connections

**Alternatives Considered**:
- Function-scoped containers: Too slow (30+ seconds per test)
- Module-scoped containers: Slightly better but still significant overhead when tests span modules
- No cleanup between tests: Violates isolation requirement (FR-003)

**Implementation Pattern**:
```python
@pytest.fixture(scope="session")
def postgres_container():
    # Container stays up for entire test session
    ...

@pytest.fixture(scope="function")
async def postgres_backend(postgres_container):
    # Fresh connection per test
    backend = PostgreSQLBackend(...)
    await backend.connect()
    yield backend
    await backend.disconnect()
```

---

### R3: How to handle the existing skipif markers and environment variables?

**Decision**: Remove skipif markers; use testcontainers by default; allow environment variable override.

**Rationale**: 
- FR-007 requires tests run without environment variables
- FR-012 requires environment variable override for debugging
- Pattern: Check env var first, fall back to testcontainers

**Alternatives Considered**:
- Keep skipif, add separate testcontainers tests: Duplicates test code
- Always use testcontainers, ignore env vars: Violates FR-012
- Parameterized fixtures: Over-engineered for this use case

**Implementation Pattern**:
```python
import os
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer | None, None, None]:
    if "POSTGRES_URL" in os.environ:
        yield None  # Use env var, no container
        return
    
    container = PostgresContainer("postgres:16")
    container.start()
    yield container
    container.stop()

@pytest.fixture
def postgres_url(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url(driver=None)
```

---

### R4: Which PostgreSQL and Redis versions to use?

**Decision**: PostgreSQL 16, Redis 7.

**Rationale**:
- Latest stable versions as of 2025
- PostgreSQL 16: Current LTS, excellent JSONB support (used by pydantic-toast)
- Redis 7: Current stable, compatible with redis-py 5.x
- Specific versions ensure reproducibility (FR-008)

**Alternatives Considered**:
- Latest tags (`:latest`): Non-deterministic, breaks reproducibility
- Older versions (PG 14, Redis 6): Unnecessary, no compatibility concerns
- Multiple version matrix: Over-engineered for library testing

**Implementation**:
```python
PostgresContainer("postgres:16")
RedisContainer("redis:7")
```

---

### R5: How to handle Docker not running errors?

**Decision**: Let testcontainers raise clear error, add helpful skip marker as fallback.

**Rationale**:
- FR-010 requires clear error messages with guidance
- testcontainers already provides reasonable errors
- pytest.skip() provides graceful degradation for CI without Docker

**Implementation Pattern**:
```python
import pytest
from testcontainers.core.container import DockerClient

@pytest.fixture(scope="session", autouse=True)
def check_docker_available():
    try:
        DockerClient().client.ping()
    except Exception as e:
        pytest.skip(
            f"Docker not available: {e}. "
            "Install Docker or set POSTGRES_URL/REDIS_URL environment variables."
        )
```

---

### R6: How to handle container connection URL format differences?

**Decision**: Transform URL to match asyncpg/redis expected format.

**Rationale**:
- PostgresContainer returns `postgresql+psycopg2://...` format
- asyncpg expects `postgresql://...` format
- Redis URL format is compatible as-is

**Implementation**:
```python
def get_postgres_url(container: PostgresContainer) -> str:
    url = container.get_connection_url()
    # asyncpg uses postgresql:// without driver suffix
    return url.replace("+psycopg2", "").replace("psycopg2://", "postgresql://")

def get_redis_url(container: RedisContainer) -> str:
    host = container.get_container_host_ip()
    port = container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"
```

---

### R7: How to integrate with existing InMemoryBackend in conftest.py?

**Decision**: Keep InMemoryBackend for unit tests; use testcontainers for integration tests.

**Rationale**:
- `test_base_model.py` tests model behavior with InMemoryBackend (fast, no external deps)
- `test_postgresql.py` and `test_redis.py` test real backend integration
- Clear separation: unit tests vs integration tests

**Implementation**:
- Keep existing `register_test_backend()` fixture for InMemoryBackend
- Add new fixtures for testcontainers that only activate for relevant test files
- Use fixture dependency to select appropriate backend

---

### R8: Package installation approach?

**Decision**: Add testcontainers to dev dependencies with database extras.

**Rationale**:
- testcontainers is a dev/test dependency, not runtime
- Use extras to pull in postgres and redis modules

**Implementation** (pyproject.toml):
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "testcontainers[postgres,redis]>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

---

## Summary of Decisions

| Topic | Decision | Key Rationale |
|-------|----------|---------------|
| Async integration | Sync containers, async operations | testcontainers is sync; db ops are async |
| Fixture scope | Session containers, function backends | Minimize startup overhead, ensure isolation |
| Env var handling | Default to containers, allow override | FR-007 + FR-012 compliance |
| Database versions | PostgreSQL 16, Redis 7 | Latest stable, reproducible |
| Docker errors | Clear message + skip option | FR-010 compliance |
| URL format | Transform for asyncpg compatibility | Driver format differences |
| Existing fixtures | Keep InMemoryBackend for unit tests | Separation of concerns |
| Installation | testcontainers in dev extras | Test-only dependency |

## References

- [testcontainers-python documentation](https://github.com/testcontainers/testcontainers-python)
- [PostgresContainer API](https://github.com/testcontainers/testcontainers-python/blob/main/docs/modules/postgres.md)
- [RedisContainer API](https://github.com/testcontainers/testcontainers-python/blob/main/docs/modules/redis.md)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
