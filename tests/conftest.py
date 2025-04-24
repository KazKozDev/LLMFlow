"""
Common test fixtures and configuration.
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

print(f"Added {project_root} to Python path")
print("Current Python path:", sys.path)

@pytest.fixture
def mock_response():
    """Create a mock response object with common attributes."""
    mock = MagicMock()
    mock.status_code = 200
    mock.json.return_value = {}
    mock.text = ""
    return mock

@pytest.fixture
def mock_cache_dir(tmp_path):
    """Create a temporary directory for cache files."""
    cache_dir = tmp_path / "test_cache"
    cache_dir.mkdir()
    return str(cache_dir)

@pytest.fixture
def sample_cache_data():
    """Return sample cache data structure."""
    return {
        'query': 'test query',
        'timestamp': datetime.now().isoformat(),
        'results': [
            {'title': 'Test Result 1', 'url': 'http://example.com/1'},
            {'title': 'Test Result 2', 'url': 'http://example.com/2'}
        ]
    }

@pytest.fixture
def mock_requests(mock_response):
    """Mock requests library."""
    with patch('requests.get', return_value=mock_response) as mock_get:
        with patch('requests.post', return_value=mock_response) as mock_post:
            yield {'get': mock_get, 'post': mock_post}

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data files."""
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return str(data_dir) 