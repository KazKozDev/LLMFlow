"""
Tests for the SearchTool class.
"""

import pytest
from tools.search_tool import SearchTool
from bs4 import BeautifulSoup
import json
from datetime import datetime
from unittest.mock import patch, Mock

def test_search_tool_initialization():
    """Test SearchTool initialization."""
    tool = SearchTool()
    assert tool.TOOL_NAME == "search_tool"
    assert isinstance(tool.user_agents, list)
    assert len(tool.user_agents) > 0
    assert hasattr(tool, 'cache_dir')

def test_get_random_user_agent():
    """Test random user agent selection."""
    tool = SearchTool()
    agent = tool.get_random_user_agent()
    assert isinstance(agent, str)
    assert agent in tool.user_agents

def test_cache_operations(mock_cache_dir, sample_cache_data):
    """Test cache operations."""
    tool = SearchTool()
    tool.cache_dir = mock_cache_dir
    query = "test query"
    
    # Test saving to cache
    tool.save_to_cache(query, sample_cache_data['results'])
    
    # Test reading from cache
    cached_results = tool.get_cached_results(query)
    assert cached_results is not None
    assert len(cached_results) == len(sample_cache_data['results'])
    assert cached_results[0]['title'] == sample_cache_data['results'][0]['title']

def test_search_web_with_cache(mock_cache_dir, sample_cache_data):
    """Test web search with cached results."""
    tool = SearchTool()
    tool.cache_dir = mock_cache_dir
    query = "test query"
    
    # Pre-populate cache
    tool.save_to_cache(query, sample_cache_data['results'])
    
    # Search should return cached results
    results = tool.search_web(query)
    assert results['query'] == query
    assert len(results['results']) > 0
    assert results['source'] == 'cache'

@patch('requests.get')
def test_search_web_with_mock_request(mock_get):
    """Test web search with mocked request."""
    tool = SearchTool()
    
    # Mock successful search response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
    <div class="result-item">
        <h3><a href="http://example.com">Test Result</a></h3>
        <div class="snippet">Test snippet</div>
    </div>
    """
    mock_get.return_value = mock_response
    
    results = tool.search_web("test query")
    assert results['query'] == "test query"
    assert isinstance(results['timestamp'], str)
    assert len(results['results']) > 0
    assert 'Test Result' in [r['title'] for r in results['results']]

@patch('requests.get')
def test_search_web_error_handling(mock_get):
    """Test error handling in web search."""
    tool = SearchTool()
    
    # Mock API error
    mock_get.side_effect = Exception("API Error")
    
    with pytest.raises(Exception) as exc_info:
        tool.search_web("test query", use_cache=False)
    assert "Error searching" in str(exc_info.value)

def test_search_web_result_limit():
    """Test limiting number of search results."""
    tool = SearchTool()
    query = "test query"
    num_results = 3
    
    # Create mock results
    mock_results = [
        {'title': f'Result {i}', 'link': f'http://example.com/{i}', 'snippet': f'Snippet {i}'}
        for i in range(5)
    ]
    
    # Mock the search method to return our results
    tool._search_html_version = lambda q: mock_results
    
    results = tool.search_web(query, num_results=num_results)
    assert len(results['results']) == num_results

@patch('requests.get')
def test_search_web_empty_results(mock_get):
    """Test handling of empty search results."""
    tool = SearchTool()
    
    # Mock empty response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html><body></body></html>"
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        tool.search_web("nonexistent query", use_cache=False)
    assert "No search results found" in str(exc_info.value)

def test_extract_html_results():
    """Test HTML results extraction."""
    tool = SearchTool()
    
    # Test HTML content
    html_content = """
    <div class="result-item">
        <h3><a href="http://example.com">Test Result</a></h3>
        <div class="snippet">Test snippet</div>
    </div>
    <div class="result-item">
        <h3><a href="http://example.com/2">Another Result</a></h3>
        <div class="snippet">Another snippet</div>
    </div>
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    results = tool._extract_html_results(str(soup))
    
    assert len(results) == 2
    assert results[0]['title'] == 'Test Result'
    assert results[1]['title'] == 'Another Result'

@patch('requests.get')
def test_search_web_with_lite_version(mock_get):
    """Test fallback to lite version."""
    tool = SearchTool()
    
    # Mock HTML version failure and lite version success
    mock_get.side_effect = [
        Exception("HTML version failed"),  # HTML version fails
        Mock(
            status_code=200,
            text='<div class="result-item"><a href="http://example.com">Test Result</a></div>'
        )  # Lite version succeeds
    ]
    
    results = tool.search_web("test query", use_cache=False)
    assert len(results['results']) > 0
    assert mock_get.call_count == 2  # Called both versions 