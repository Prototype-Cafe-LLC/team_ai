"""Test configuration and fixtures."""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.state import StateManager
from app.core.events import EventBus
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def state_manager() -> AsyncGenerator[StateManager, None]:
    """Create test state manager."""
    manager = StateManager()
    await manager.connect()
    yield manager
    await manager.disconnect()


@pytest.fixture
def event_bus() -> EventBus:
    """Create test event bus."""
    return EventBus()


@pytest.fixture
def test_project_requirements() -> str:
    """Sample project requirements for testing."""
    return """
    Create a simple todo list application with the following features:
    1. Users can add new todo items
    2. Users can mark items as complete
    3. Users can delete items
    4. Items should persist between sessions
    """


@pytest.fixture
def mock_llm_response() -> dict:
    """Mock LLM response for testing."""
    return {
        "requirements": {
            "content": "## Requirements Document\\n1. Add todos\\n2. Complete todos\\n3. Delete todos",
            "approved": True
        },
        "design": {
            "content": "## System Design\\n- REST API\\n- PostgreSQL database\\n- React frontend",
            "approved": True
        },
        "implementation": {
            "content": "## Implementation\\n```python\\n# Todo API implementation\\n```",
            "approved": True
        },
        "test": {
            "content": "## Test Suite\\n```python\\n# Test cases\\n```",
            "approved": True
        }
    }