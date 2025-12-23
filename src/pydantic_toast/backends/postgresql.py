"""PostgreSQL storage backend using asyncpg."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from pydantic_toast.backends.base import StorageBackend
from pydantic_toast.exceptions import ExternalStorageError, StorageConnectionError


def _load_sql(filename: str) -> str:
    """Load SQL query from file."""
    sql_dir = Path(__file__).parent / "sql"
    sql_file = sql_dir / filename
    return sql_file.read_text()


class PostgreSQLBackend(StorageBackend):
    """PostgreSQL storage backend using asyncpg.

    Stores model data in a JSONB column for efficient querying.
    Uses connection pooling for performance.
    """

    def __init__(self, url: str) -> None:
        super().__init__(url)
        self._pool: Any = None
        self._sql_upsert = _load_sql("upsert_model.sql")
        self._sql_select = _load_sql("select_model.sql")
        self._sql_create_table = _load_sql("create_table.sql")
        self._sql_create_index = _load_sql("create_index.sql")

    async def connect(self) -> None:
        """Initialize connection pool and create table if needed."""
        try:
            import asyncpg
        except ImportError as e:
            raise StorageConnectionError(
                "asyncpg is not installed. Install with: pip install pydantic-toast[postgresql]",
                url=self._url,
                cause=e,
            ) from e

        try:
            self._pool = await asyncpg.create_pool(self._url)
            await self._ensure_table()
        except Exception as e:
            raise StorageConnectionError(
                f"Failed to connect to PostgreSQL: {e}",
                url=self._url,
                cause=e,
            ) from e

    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def save(self, id: UUID, class_name: str, data: dict[str, Any]) -> None:
        """Persist model data using UPSERT query."""
        if self._pool is None:
            raise StorageConnectionError("Not connected to PostgreSQL", url=self._url)

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(
                    self._sql_upsert,
                    id,
                    class_name,
                    json.dumps(data),
                    data.get("schema_version", 1),
                    datetime.now(UTC),
                )
        except Exception as e:
            raise ExternalStorageError(f"Failed to save record: {e}") from e

    async def load(self, id: UUID, class_name: str) -> dict[str, Any] | None:
        """Retrieve model data from PostgreSQL."""
        if self._pool is None:
            raise StorageConnectionError("Not connected to PostgreSQL", url=self._url)

        try:
            async with self._pool.acquire() as conn:
                row = await conn.fetchrow(
                    self._sql_select,
                    id,
                    class_name,
                )
                if row is None:
                    return None
                data = row["data"]
                if isinstance(data, str):
                    return json.loads(data)
                return dict(data)
        except Exception as e:
            raise ExternalStorageError(f"Failed to load record: {e}") from e

    async def _ensure_table(self) -> None:
        """Create external_models table if it doesn't exist."""
        if self._pool is None:
            return

        async with self._pool.acquire() as conn:
            await conn.execute(self._sql_create_table)
            await conn.execute(self._sql_create_index)
