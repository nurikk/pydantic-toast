"""Test fixtures for pydantic-toast tests."""

import asyncio
from collections.abc import AsyncGenerator
from typing import Any

import pytest


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    """Use the default event loop policy for all tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(scope="function")
async def mock_storage() -> AsyncGenerator[dict[str, Any], None]:
    """In-memory storage for testing without external dependencies."""
    storage: dict[str, Any] = {}
    yield storage
    storage.clear()
