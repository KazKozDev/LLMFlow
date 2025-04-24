"""
Tests for the WikipediaTool class.
"""

import pytest
from unittest.mock import Mock, patch
from tools.wikipedia_tool import WikipediaTool

def test_wikipedia_tool_initialization():
    """Test WikipediaTool initialization."""
    tool = WikipediaTool()
    assert tool.TOOL_NAME == "wikipedia_tool"
    assert "Wikipedia" in tool.TOOL_DESCRIPTION
    assert hasattr(tool, 'cache_expiry')
    assert hasattr(tool, 'language')
    assert hasattr(tool, 'user_agent')

@patch('requests.get')
def test_search_wikipedia(mock_get):
    """Test Wikipedia search functionality."""
    tool = WikipediaTool()
    
    # Mock successful search response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'query': {
            'search': [
                {
                    'title': 'Python (programming language)',
                    'snippet': 'Python is a high-level programming language...',
                    'pageid': 23862
                }
            ]
        }
    }
    mock_get.return_value = mock_response
    
    results = tool.search_wikipedia("Python programming")
    
    assert len(results) > 0
    assert 'title' in results[0]
    assert 'snippet' in results[0]
    assert 'pageid' in results[0]
    
    # Verify API call
    called_url = mock_get.call_args[0][0]
    assert 'action=query' in called_url
    assert 'list=search' in called_url
    assert 'srsearch=Python+programming' in called_url

@patch('requests.get')
def test_get_article_content(mock_get):
    """Test retrieving article content."""
    tool = WikipediaTool()
    
    # Mock article content response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'query': {
            'pages': {
                '23862': {
                    'extract': 'Python is a programming language...',
                    'title': 'Python (programming language)',
                    'pageid': 23862
                }
            }
        }
    }
    mock_get.return_value = mock_response
    
    content = tool.get_article_content(23862)
    
    assert content['title'] == 'Python (programming language)'
    assert content['content'].startswith('Python is a programming language')
    assert content['pageid'] == 23862
    
    # Verify API call
    called_url = mock_get.call_args[0][0]
    assert 'action=query' in called_url
    assert 'prop=extracts' in called_url
    assert 'pageids=23862' in called_url

def test_cache_functionality():
    """Test caching functionality."""
    tool = WikipediaTool()
    
    # Create test article content
    test_content = {
        'title': 'Test Article',
        'content': 'Test content...',
        'pageid': 12345
    }
    
    # Store in cache
    tool._cache_article(12345, test_content)
    
    # Retrieve from cache
    cached_content = tool._get_cached_article(12345)
    assert cached_content == test_content

@patch('requests.get')
def test_error_handling(mock_get):
    """Test error handling."""
    tool = WikipediaTool()
    
    # Mock error response
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.json.return_value = {
        'error': {
            'code': 'invalid',
            'info': 'Invalid search term'
        }
    }
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        tool.search_wikipedia("")
    assert "Error searching Wikipedia" in str(exc_info.value)
    
    # Mock network error
    mock_get.side_effect = Exception("Network error")
    with pytest.raises(Exception) as exc_info:
        tool.search_wikipedia("test")
    assert "Failed to connect to Wikipedia" in str(exc_info.value)

def test_language_support():
    """Test language support."""
    tool = WikipediaTool()
    tool.set_language("ru")
    assert tool.language == "ru"
    assert "ru.wikipedia.org" in tool._get_api_url()

def test_invalid_language():
    """Test handling of invalid language code."""
    tool = WikipediaTool()
    with pytest.raises(ValueError) as exc_info:
        tool.set_language("invalid")
    assert "Invalid language code" in str(exc_info.value)

@patch('requests.get')
def test_search_with_limit(mock_get):
    """Test search with result limit."""
    tool = WikipediaTool()
    
    # Mock search response with multiple results
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'query': {
            'search': [
                {'title': 'Result 1', 'snippet': 'Snippet 1', 'pageid': 1},
                {'title': 'Result 2', 'snippet': 'Snippet 2', 'pageid': 2},
                {'title': 'Result 3', 'snippet': 'Snippet 3', 'pageid': 3}
            ]
        }
    }
    mock_get.return_value = mock_response
    
    results = tool.search_wikipedia("test", limit=2)
    assert len(results) == 2
    
    # Verify limit parameter in API call
    called_url = mock_get.call_args[0][0]
    assert 'srlimit=2' in called_url

@patch('requests.get')
def test_empty_search_results(mock_get):
    """Test handling of empty search results."""
    tool = WikipediaTool()
    
    # Mock empty search response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'query': {
            'search': []
        }
    }
    mock_get.return_value = mock_response
    
    results = tool.search_wikipedia("nonexistent_topic_12345")
    assert len(results) == 0

@patch('requests.get')
def test_article_not_found(mock_get):
    """Test handling of non-existent article."""
    tool = WikipediaTool()
    
    # Mock response for non-existent article
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'query': {
            'pages': {
                '-1': {
                    'missing': ''
                }
            }
        }
    }
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        tool.get_article_content(99999)
    assert "Article not found" in str(exc_info.value) 