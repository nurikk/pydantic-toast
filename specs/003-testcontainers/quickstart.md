# Quickstart: Testcontainers Integration

**Feature**: 003-testcontainers  
**Date**: 2025-12-23

## Prerequisites

1. **Docker**: Docker Desktop (macOS/Windows) or Docker Engine (Linux) must be installed and running
2. **Python 3.13+**: As required by pydantic-toast
3. **uv**: Package manager (recommended) or pip

## Installation

```bash
# Install dev dependencies including testcontainers
uv sync --dev

# Or with pip
pip install -e ".[dev]"
```

## Running Tests

### Default: Using Testcontainers (Recommended)

Simply run pytest - containers are managed automatically:

```bash
# Run all tests
pytest

# Run only PostgreSQL tests
pytest tests/test_postgresql.py

# Run only Redis tests
pytest tests/test_redis.py

# Run with verbose output
pytest -v

# Run tests in parallel (faster execution)
pytest -n auto
```

**What happens automatically**:
1. Docker availability is checked
2. PostgreSQL 16 container starts (~5-10 seconds)
3. Redis 7 container starts (~2-5 seconds)
4. Tests execute against real databases
5. Containers are cleaned up after tests complete

### Parallel Test Execution

For faster test execution, use pytest-xdist to run tests in parallel:

```bash
# Install pytest-xdist (if not already installed)
uv pip install pytest-xdist

# Run with auto-detected worker count
pytest -n auto

# Run with specific number of workers
pytest -n 4
```

**How it works**:
- Each parallel worker gets its own isolated database containers
- No port conflicts or data contamination between workers
- Typically 2-4x faster than sequential execution
- Session-scoped containers ensure minimal startup overhead

## Troubleshooting

### Docker Not Running

**Error**: `Docker not available: ...`

**Solution**:
```bash
# macOS/Windows: Start Docker Desktop

# Linux: Start Docker daemon
sudo systemctl start docker

# Verify Docker is running
docker ps
```

### Container Startup Timeout

**Error**: `TimeoutError: Container did not start within...`

**Solution**:
```bash
# Pre-pull images to avoid download during tests
docker pull postgres:16
docker pull redis:7

# Or increase timeout (in seconds)
export TC_MAX_TRIES=60
export TC_POOLING_INTERVAL=2
pytest
```

### Port Conflicts

**Error**: `Port already in use`

**Solution**: Testcontainers uses dynamic port allocation, so this is rare. If it happens:
```bash
# Check what's using common ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill the process or use different ports for local services
```

### Permission Denied

**Error**: `Permission denied while connecting to Docker`

**Solution**:
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in

# Or run with sudo (not recommended)
sudo pytest
```

## Expected Test Output

```
$ pytest -v

tests/test_base_model.py::test_external_base_model_creates_id PASSED
tests/test_base_model.py::test_model_dump_returns_reference PASSED
tests/test_base_model.py::test_model_validate_restores_model PASSED
tests/test_postgresql.py::test_postgresql_backend_connect_creates_pool PASSED
tests/test_postgresql.py::test_postgresql_backend_save_stores_data PASSED
tests/test_postgresql.py::test_postgresql_backend_load_retrieves_data PASSED
tests/test_postgresql.py::test_full_round_trip_with_postgresql_backend PASSED
tests/test_redis.py::test_redis_backend_connect_creates_client PASSED
tests/test_redis.py::test_redis_backend_save_stores_data PASSED
tests/test_redis.py::test_redis_backend_load_retrieves_data PASSED
tests/test_redis.py::test_full_round_trip_with_redis_backend PASSED
tests/test_registry.py::test_global_registry_singleton PASSED

========================= 12 passed in 45.23s =========================
```

## Performance Notes

| Operation | Expected Time |
|-----------|---------------|
| First test run (pulling images) | 30-60 seconds |
| Subsequent runs (images cached) | 10-20 seconds |
| Container startup overhead | ~5-10 seconds |
| Individual test execution | <1 second |

**Tips for faster tests**:
- Keep Docker running between test runs
- Pre-pull images: `docker pull postgres:16 && docker pull redis:7`
- Use session-scoped fixtures (default) to share containers across tests
