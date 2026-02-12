"""
Pytest configuration and fixtures for the Mergington High School API tests.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Fixture that provides a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Fixture that resets the activities database before each test.
    This ensures test isolation by providing a clean state.
    """
    # Store original state
    original_activities = {
        key: {
            "description": val["description"],
            "schedule": val["schedule"],
            "max_participants": val["max_participants"],
            "participants": val["participants"].copy()
        }
        for key, val in activities.items()
    }
    
    yield
    
    # Restore original state
    for key, val in original_activities.items():
        activities[key]["participants"] = val["participants"]
