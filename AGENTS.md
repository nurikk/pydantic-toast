# pydantic-toast Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-23

## Active Technologies
- Python 3.13+ + pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis) (001-external-storage)
- PostgreSQL (JSONB), Redis (JSON strings) (001-external-storage)
- Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`) + pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis) (002-sync-methods-support)
- Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`) + estcontainers[postgres,redis], asyncpg>=0.29.0, redis>=5.0.0, pytest>=8.0.0, pytest-asyncio>=0.23.0 (003-testcontainers)
- PostgreSQL (via testcontainers), Redis (via testcontainers) (003-testcontainers)

- (001-external-storage)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

# Add commands for 

## Code Style

: Follow standard conventions

## Recent Changes
- 003-testcontainers: Added Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`) + estcontainers[postgres,redis], asyncpg>=0.29.0, redis>=5.0.0, pytest>=8.0.0, pytest-asyncio>=0.23.0
- 002-sync-methods-support: Added Python 3.13+ (as per pyproject.toml `requires-python = ">=3.13"`) + pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis)
- 001-external-storage: Added Python 3.13+ + pydantic>=2.0.0, asyncpg>=0.29.0 (PostgreSQL), redis>=5.0.0 (Redis)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
