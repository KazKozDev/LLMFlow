"""
Tests for the CurrencyTool class.
"""

import pytest
from tools.currency_tool import CurrencyTool
from datetime import datetime

def test_currency_tool_initialization():
    """Test CurrencyTool initialization."""
    tool = CurrencyTool()
    assert tool.TOOL_NAME == "currency_tool"
    assert tool.exchange_rates_url.startswith("https://")
    assert tool.backup_api_url.startswith("https://")
    assert tool.cache_expiry == 3600

def test_standardize_currency_code():
    """Test currency code standardization."""
    tool = CurrencyTool()
    
    # Test standard codes
    assert tool._standardize_currency_code("USD") == "USD"
    assert tool._standardize_currency_code("EUR") == "EUR"
    
    # Test common variations
    assert tool._standardize_currency_code("dollar") == "USD"
    assert tool._standardize_currency_code("euros") == "EUR"
    assert tool._standardize_currency_code("pounds") == "GBP"
    
    # Test Russian variations
    assert tool._standardize_currency_code("рубль") == "RUB"
    assert tool._standardize_currency_code("₽") == "RUB"
    
    # Test with whitespace and case
    assert tool._standardize_currency_code(" usd ") == "USD"
    assert tool._standardize_currency_code("Eur") == "EUR"

def test_convert_currency(mock_requests):
    """Test currency conversion."""
    tool = CurrencyTool()
    
    # Mock exchange rates response
    mock_response = {
        'result': 'success',
        'rates': {
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0
        }
    }
    mock_requests['get'].return_value.json.return_value = mock_response
    
    # Test USD to EUR conversion
    result = tool.convert_currency(100, "USD", "EUR")
    assert result['query']['amount'] == 100
    assert result['query']['from'] == "USD"
    assert result['query']['to'] == "EUR"
    assert result['result']['amount'] == pytest.approx(85.0)
    
    # Verify request was made
    mock_requests['get'].assert_called_once()

def test_get_exchange_rates(mock_requests):
    """Test exchange rates retrieval."""
    tool = CurrencyTool()
    
    # Mock response
    mock_response = {
        'result': 'success',
        'rates': {
            'EUR': 0.85,
            'GBP': 0.73,
            'JPY': 110.0
        }
    }
    mock_requests['get'].return_value.json.return_value = mock_response
    
    rates = tool.get_exchange_rates("USD")
    
    assert rates['base_currency'] == "USD"
    assert 'rates' in rates
    assert isinstance(rates['timestamp'], str)
    assert rates['rates']['EUR'] == 0.85

def test_cache_functionality():
    """Test caching functionality."""
    tool = CurrencyTool()
    
    # Create test exchange rates
    test_rates = {
        'EUR': 0.85,
        'GBP': 0.73
    }
    
    # Store in cache
    cache_key = "USD"
    tool.exchange_rates_cache[cache_key] = test_rates
    tool.cache_timestamp[cache_key] = datetime.now().timestamp()
    
    # Test conversion using cached rates
    result = tool.convert_currency(100, "USD", "EUR")
    assert result['result']['amount'] == pytest.approx(85.0)

def test_error_handling(mock_requests):
    """Test error handling."""
    tool = CurrencyTool()
    
    # Mock API error responses
    mock_requests['get'].side_effect = [
        type('MockResponse', (), {
            'json': lambda: {'result': 'error', 'error': 'Primary API Error'},
            'raise_for_status': lambda: None
        }),
        type('MockResponse', (), {
            'json': lambda: {'success': False, 'error': {'info': 'Backup API Error'}},
            'raise_for_status': lambda: None
        })
    ]
    
    with pytest.raises(Exception) as exc_info:
        tool.convert_currency(100, "USD", "EUR")
    assert "Error in currency conversion" in str(exc_info.value)

def test_invalid_currency_codes():
    """Test handling of invalid currency codes."""
    tool = CurrencyTool()
    
    # Create test rates with only valid currencies
    tool.exchange_rates_cache["USD"] = {
        'EUR': 0.85,
        'GBP': 0.73
    }
    tool.cache_timestamp["USD"] = datetime.now().timestamp()
    
    with pytest.raises(Exception) as exc_info:
        tool.convert_currency(100, "INVALID", "EUR")
    assert "Currency 'INVALID' is not supported" in str(exc_info.value)

def test_backup_api_fallback(mock_requests):
    """Test fallback to backup API."""
    tool = CurrencyTool()
    
    # Mock primary API failure and backup API success
    mock_requests['get'].side_effect = [
        type('MockResponse', (), {
            'json': lambda: {'result': 'error', 'error': 'Primary API Error'},
            'raise_for_status': lambda: None
        }),
        type('MockResponse', (), {
            'json': lambda: {'success': True, 'rates': {'EUR': 0.85}},
            'raise_for_status': lambda: None
        })
    ]
    
    result = tool.convert_currency(100, "USD", "EUR")
    assert result['result']['amount'] == pytest.approx(85.0)
    assert mock_requests['get'].call_count == 2  # Called both APIs

def test_zero_amount_conversion():
    """Test conversion of zero amount."""
    tool = CurrencyTool()
    
    # Mock exchange rates
    tool.exchange_rates_cache["USD"] = {'EUR': 0.85}
    tool.cache_timestamp["USD"] = datetime.now().timestamp()
    
    result = tool.convert_currency(0, "USD", "EUR")
    assert result['result']['amount'] == 0
    assert result['result']['formatted'] == "0.00 EUR"

def test_same_currency_conversion():
    """Test conversion between same currencies."""
    tool = CurrencyTool()
    
    result = tool.convert_currency(100, "USD", "USD")
    assert result['result']['amount'] == 100
    assert result['info']['rate'] == 1.0 