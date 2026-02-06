import pytest
from unittest.mock import MagicMock
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_settings():
    """Mock the settings object"""
    with pytest.MonkeyPatch.context() as m:
        m.setenv("JWT_SECRET_KEY", "test_secret_key_123")
        m.setenv("JWT_ALGORITHM", "HS256")
        yield

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    mock = MagicMock()
    return mock
