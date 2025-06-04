# Backend Tests Configuration
import pytest
import asyncio
from typing import Generator
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_user_data():
    """Mock user data for testing."""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "role": "USER",
        "isActive": True,
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
    }

@pytest.fixture
def mock_credentials():
    """Mock credentials for testing."""
    return {
        "email": "test@example.com",
        "password": "test123"
    }

@pytest.fixture
def invalid_credentials():
    """Invalid credentials for testing."""
    return {
        "email": "invalid@example.com",
        "password": "wrongpassword"
    }
