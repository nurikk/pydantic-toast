# Data Model: Testcontainers Integration

**Feature**: 003-testcontainers  
**Date**: 2025-12-23

## Overview

This feature introduces no new persistent data models. Instead, it defines **test infrastructure entities** that manage ephemeral container lifecycle and provide connection parameters to tests.

## Entities

### 1. PostgresContainer (External - from testcontainers)

An ephemeral PostgreSQL database instance running in a Docker container.

| Attribute | Type | Description |
|-----------|------|-------------|
| image | str | Docker image name (e.g., "postgres:16") |
| port | int | Internal container port (5432) |
| username | str | Database username (default: "test") |
| password | str | Database password (default: "test") |
| dbname | str | Database name (default: "test") |

**Lifecycle**:
- Created: `container.start()` - Starts Docker container, waits for readiness
- Active: Container running, accepting connections
- Destroyed: `container.stop()` - Stops and removes container

**Methods**:
- `get_connection_url() -> str`: Returns SQLAlchemy-style connection URL
- `get_container_host_ip() -> str`: Returns host IP for container access
- `get_exposed_port(port: int) -> int`: Returns mapped host port

---

### 2. RedisContainer (External - from testcontainers)

An ephemeral Redis instance running in a Docker container.

| Attribute | Type | Description |
|-----------|------|-------------|
| image | str | Docker image name (e.g., "redis:7") |
| port | int | Internal container port (6379) |

**Lifecycle**:
- Created: `container.start()` - Starts Docker container, waits for readiness
- Active: Container running, accepting connections
- Destroyed: `container.stop()` - Stops and removes container

**Methods**:
- `get_container_host_ip() -> str`: Returns host IP for container access
- `get_exposed_port(port: int) -> int`: Returns mapped host port

---

### 3. TestFixtureState (Internal - pytest fixture state)

Represents the test infrastructure state during a test session.

| Attribute | Type | Description |
|-----------|------|-------------|
| postgres_container | PostgresContainer \| None | Active PostgreSQL container (None if using env var) |
| redis_container | RedisContainer \| None | Active Redis container (None if using env var) |
| postgres_url | str | Connection URL for PostgreSQL backend |
| redis_url | str | Connection URL for Redis backend |

**State Transitions**:

```
┌─────────────┐     start()      ┌─────────────┐
│   Initial   │ ───────────────► │   Active    │
│ (no container)                  │ (container  │
└─────────────┘                   │  running)   │
                                  └──────┬──────┘
                                         │ stop()
                                         ▼
                                  ┌─────────────┐
                                  │  Destroyed  │
                                  │ (container  │
                                  │  removed)   │
                                  └─────────────┘
```

---

## Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Session                             │
│                                                              │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │ PostgresContainer│         │  RedisContainer │            │
│  │   (session)      │         │    (session)    │            │
│  └────────┬─────────┘         └────────┬────────┘            │
│           │                            │                     │
│           │ provides URL               │ provides URL        │
│           ▼                            ▼                     │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │ PostgreSQLBackend│         │  RedisBackend   │            │
│  │   (function)     │         │   (function)    │            │
│  └────────┬─────────┘         └────────┬────────┘            │
│           │                            │                     │
│           │ used by                    │ used by             │
│           ▼                            ▼                     │
│  ┌─────────────────┐         ┌─────────────────┐            │
│  │test_postgresql.py│         │ test_redis.py   │            │
│  └──────────────────┘         └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Validation Rules

### Container Startup

1. Docker daemon must be running and accessible
2. Container image must be pullable (network access or local cache)
3. Container must respond to health check within timeout (default: 120s)
4. Port binding must succeed (dynamic port allocation handles conflicts)

### Connection URLs

1. PostgreSQL URL must match format: `postgresql://{user}:{password}@{host}:{port}/{dbname}`
2. Redis URL must match format: `redis://{host}:{port}/{db}`
3. URLs must be valid and parseable by respective client libraries

### Environment Variable Override

1. If `POSTGRES_URL` is set, no PostgreSQL container is started
2. If `REDIS_URL` is set, no Redis container is started
3. Environment URLs must be valid connection strings

## No Persistent State

This feature introduces no database schema changes. All entities are ephemeral:

- Containers exist only during test session
- Database contents are lost when containers stop
- No migrations required
- No data persistence between test runs
