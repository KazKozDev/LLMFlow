import pytest
import unittest.mock
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the tool class and functions to be tested
from tools.stock_tool import (
    StockTool, 
    get_stock_quote, # Correct function name
    get_company_info, 
    get_historical_data,
    get_market_summary,
    calculate_technical_indicator,
    search_stocks
)

# --- Mock Data ---

# Mock data for the internal StockTool.get_stock_quote method result
MOCK_QUOTE_DATA_AAPL = {
    'symbol': 'AAPL',
    'name': 'Apple Inc.',
    'price': 175.50,
    'change': 1.20,
    'change_percent': 0.69,
    'volume': 50000000,
    'market_cap': 2.75e12,
    'open': 174.80,
    'high': 176.00,
    'low': 174.50,
    'previous_close': 174.30,
    'timestamp': datetime(2024, 4, 24, 16, 0, 0).isoformat(),
    'source': 'MockAPI'
}

# Mock data for StockTool.get_company_info
MOCK_COMPANY_INFO_MSFT = {
    'symbol': 'MSFT',
    'name': 'Microsoft Corporation',
    # Nest profile data as expected by the description formatter
    'profile': {
        'sector': 'Technology',
        'industry': 'Software—Infrastructure',
        'description': 'Microsoft Corporation develops, licenses, and supports software...',
        'ceo': 'Mr. Satya Nadella',
        'employees': 221000,
        'headquarters': 'One Microsoft Way, Redmond, WA, USA', # Changed from hq_address
        'website': 'http://www.microsoft.com'
    },
    # Add other potential top-level keys if the formatter uses them (e.g., financials, key_stats)
    'financials': {},
    'key_statistics': {},
    'dividend_data': {},
    'timestamp': datetime(2024, 4, 24, 15, 0, 0).isoformat(),
    'source': 'MockAPI' # The formatter uses 'data_source', maybe rename here or fix formatter?
                       # Let's keep 'source' for now and see if tests pass/fail.
}

# Mock data for StockTool.search_stocks
MOCK_SEARCH_STOCKS_RESULT = [
    {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'exchange': 'NASDAQ'},
    {'symbol': 'NVDA.L', 'name': 'NVIDIA Corp', 'exchange': 'LSE'}
]

# Mock data for StockTool.get_historical_data
MOCK_HISTORICAL_DATA_AMZN = {
    'symbol': 'AMZN',
    'name': 'Amazon.com Inc.',
    'period': '1month',
    'time_series': [
        {'date': '2024-03-25', 'open': 180.0, 'close': 181.0, 'high': 182.0, 'low': 179.5, 'volume': 30000000},
        {'date': '2024-03-26', 'open': 181.5, 'close': 183.0, 'high': 183.5, 'low': 181.0, 'volume': 35000000}
        # ... more data points ...
    ],
    'performance': {
        'start_price': 180.0,
        'end_price': 183.0,
        'change': 3.0,
        'change_percent': 1.67,
        'max_price': 183.5,
        'min_price': 179.5,
        'trading_days': 2 # Simplified for mock data
    },
    'currency': 'USD',
    'data_source': 'MockAPI',
    'timestamp': datetime(2024, 4, 24, 17, 0, 0).isoformat()
}

# Mock data for StockTool.get_market_summary
MOCK_MARKET_SUMMARY_DATA = {
    "market_direction": "UP",
    "indices": [
        {"symbol": "^GSPC", "name": "S&P 500", "price": 5000.0, "change": 25.0, "percent_change": 0.5},
        {"symbol": "^DJI", "name": "Dow Jones", "price": 38000.0, "change": 150.0, "percent_change": 0.39}
    ],
    "sector_performance": [
        {"name": "Technology", "change": 1.2},
        {"name": "Energy", "change": -0.5}
    ],
    "data_source": "MockAPI",
    "timestamp": datetime(2024, 4, 24, 16, 30, 0).isoformat(),
    "market_time": "April 24, 2024"
}

# Mock data for StockTool.calculate_technical_indicator
MOCK_INDICATOR_DATA_RSI = {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "indicator": "RSI",
    "period": 14,
    "latest_value": 65.5,
    "interpretation": "The RSI indicator is in the neutral zone...",
    "values": [50.0, 55.0, 60.0, 65.5],
    "dates": ["2024-04-21", "2024-04-22", "2024-04-23", "2024-04-24"],
    "data_source": "MockAPI",
    "timestamp": datetime(2024, 4, 24, 16, 45, 0).isoformat()
}

# --- Test Class ---
class TestStockTool:

    @patch('tools.stock_tool.StockTool.get_stock_quote')
    def test_get_stock_quote_success(self, mock_internal_quote):
        """Test the get_stock_quote wrapper function for success."""
        mock_internal_quote.return_value = MOCK_QUOTE_DATA_AAPL
        symbol = "AAPL"
        
        result_str = get_stock_quote(symbol)
        
        mock_internal_quote.assert_called_once_with(symbol)
        
        # Check the formatted string output - Adjust assertions based on actual format
        assert "Apple Inc. (AAPL)" in result_str
        assert "Price: 175.50 USD" in result_str # Updated format
        assert "(+1.20 (+0.69%))" in result_str # Check change format
        assert "Volume: 50.00M" in result_str # Check volume format
        assert "Market Cap: $2.75T" in result_str # Check market cap format (seems correct)

    @patch('tools.stock_tool.StockTool.get_stock_quote')
    def test_get_stock_quote_not_found(self, mock_internal_quote):
        """Test get_stock_quote wrapper when the symbol is not found."""
        error_message = "Stock symbol 'INVALID' not found."
        mock_internal_quote.side_effect = Exception(error_message)
        symbol = "INVALID"
        
        result_str = get_stock_quote(symbol)
        
        mock_internal_quote.assert_called_once_with(symbol)
        assert f"Error getting stock quote: {error_message}" in result_str

    @patch('tools.stock_tool.StockTool.get_stock_quote')
    def test_get_stock_quote_api_error(self, mock_internal_quote):
        """Test get_stock_quote wrapper when the API fails."""
        error_message = "API request failed: Timeout"
        mock_internal_quote.side_effect = Exception(error_message)
        symbol = "AAPL"
        
        result_str = get_stock_quote(symbol)
        
        mock_internal_quote.assert_called_once_with(symbol)
        assert f"Error getting stock quote: {error_message}" in result_str

    # --- Tests for get_company_info ---

    @patch('tools.stock_tool.StockTool.get_company_info')
    def test_get_company_info_success(self, mock_internal_info):
        """Test the get_company_info wrapper function for success."""
        mock_internal_info.return_value = MOCK_COMPANY_INFO_MSFT
        symbol = "MSFT"
        result_str = get_company_info(symbol)
        mock_internal_info.assert_called_once_with(symbol)
        assert "Microsoft Corporation (MSFT)" in result_str
        assert "Sector: Technology" in result_str
        assert "Industry: Software—Infrastructure" in result_str
        assert "Employees: 221000" in result_str
        assert "Website: http://www.microsoft.com" in result_str

    @patch('tools.stock_tool.StockTool.get_company_info')
    def test_get_company_info_not_found(self, mock_internal_info):
        """Test get_company_info wrapper when the symbol is not found."""
        error_message = "Company symbol 'INVALID' not found."
        mock_internal_info.side_effect = Exception(error_message)
        symbol = "INVALID"
        result_str = get_company_info(symbol)
        mock_internal_info.assert_called_once_with(symbol)
        assert f"Error getting company information: {error_message}" in result_str

    # --- Tests for search_stocks ---

    @patch('tools.stock_tool.StockTool.search_stocks')
    def test_search_stocks_success(self, mock_internal_search):
        """Test the search_stocks wrapper function for success."""
        mock_internal_search.return_value = MOCK_SEARCH_STOCKS_RESULT
        query = "Nvidia"
        limit = 5
        result_str = search_stocks(query, limit)
        mock_internal_search.assert_called_once_with(query, limit)
        assert f"Found 2 stock matches for 'Nvidia'" in result_str
        assert "1. NVIDIA Corporation (NVDA) - NASDAQ" in result_str
        assert "2. NVIDIA Corp (NVDA.L) - LSE" in result_str

    @patch('tools.stock_tool.StockTool.search_stocks')
    def test_search_stocks_no_results(self, mock_internal_search):
        """Test search_stocks wrapper when no results are found."""
        mock_internal_search.return_value = [] # Empty list for no results
        query = "NonExistentCompany"
        limit = 5
        result_str = search_stocks(query, limit)
        mock_internal_search.assert_called_once_with(query, limit)
        assert f"No stock matches found for 'NonExistentCompany'" in result_str

    @patch('tools.stock_tool.StockTool.search_stocks')
    def test_search_stocks_api_error(self, mock_internal_search):
        """Test search_stocks wrapper when the API fails."""
        error_message = "Search API error"
        mock_internal_search.side_effect = Exception(error_message)
        query = "Nvidia"
        limit = 5
        result_str = search_stocks(query, limit)
        mock_internal_search.assert_called_once_with(query, limit)
        assert f"Error searching stocks: {error_message}" in result_str

    # --- Tests for get_historical_data ---

    @patch('tools.stock_tool.StockTool.get_historical_data')
    def test_get_historical_data_success(self, mock_internal_hist):
        """Test the get_historical_data wrapper function for success."""
        mock_internal_hist.return_value = MOCK_HISTORICAL_DATA_AMZN
        symbol = "AMZN"
        period = "1month"
        result_str = get_historical_data(symbol, period)
        mock_internal_hist.assert_called_once_with(symbol, period)
        assert "Historical Data for Amazon.com Inc. (AMZN) - 1month" in result_str
        # Use dates from mock data for assertion
        start_date = MOCK_HISTORICAL_DATA_AMZN['time_series'][0]['date']
        end_date = MOCK_HISTORICAL_DATA_AMZN['time_series'][-1]['date']
        assert f"PERFORMANCE SUMMARY ({start_date} to {end_date})" in result_str
        assert "Change: +3.00 (+1.67%) USD" in result_str
        assert "The stock is up over this period." in result_str
        assert "High: 183.50 USD" in result_str

    @patch('tools.stock_tool.StockTool.get_historical_data')
    def test_get_historical_data_no_data(self, mock_internal_hist):
        """Test get_historical_data wrapper when no data is returned."""
        # Simulate no data by returning a structure with an empty time_series
        mock_no_data = MOCK_HISTORICAL_DATA_AMZN.copy()
        mock_no_data['time_series'] = []
        mock_no_data['performance'] = {}
        mock_no_data['name'] = 'Amazon.com Inc.' # Ensure name is present for error message
        mock_no_data['symbol'] = 'AMZN'
        mock_internal_hist.return_value = mock_no_data
        symbol = "AMZN"
        period = "1month"
        result_str = get_historical_data(symbol, period)
        mock_internal_hist.assert_called_once_with(symbol, period)
        assert f"No historical data available for Amazon.com Inc. (AMZN)." in result_str

    @patch('tools.stock_tool.StockTool.get_historical_data')
    def test_get_historical_data_api_error(self, mock_internal_hist):
        """Test get_historical_data wrapper when the API fails."""
        error_message = "Historical API error"
        mock_internal_hist.side_effect = Exception(error_message)
        symbol = "AMZN"
        period = "1month"
        result_str = get_historical_data(symbol, period)
        mock_internal_hist.assert_called_once_with(symbol, period)
        assert f"Error getting historical data: {error_message}" in result_str

    # --- Tests for get_market_summary ---
    
    @patch('tools.stock_tool.StockTool.get_market_summary')
    def test_get_market_summary_success(self, mock_internal_summary):
        """Test the get_market_summary wrapper function for success."""
        mock_internal_summary.return_value = MOCK_MARKET_SUMMARY_DATA
        result_str = get_market_summary()
        mock_internal_summary.assert_called_once()
        assert "Market Summary as of April 24, 2024" in result_str
        assert "Overall Market: UP" in result_str
        assert "S&P 500: 5000.00 +25.00 (+0.50%)" in result_str # Check index formatting
        assert "Technology: +1.20%" in result_str # Check sector formatting

    @patch('tools.stock_tool.StockTool.get_market_summary')
    def test_get_market_summary_api_error(self, mock_internal_summary):
        """Test get_market_summary wrapper when the API fails."""
        error_message = "Market Summary API error"
        mock_internal_summary.side_effect = Exception(error_message)
        result_str = get_market_summary()
        mock_internal_summary.assert_called_once()
        assert f"Error getting market summary: {error_message}" in result_str
        
    # --- Tests for calculate_technical_indicator ---
    
    @patch('tools.stock_tool.StockTool.get_technical_indicator')
    def test_calculate_technical_indicator_success(self, mock_internal_indicator):
        """Test the calculate_technical_indicator wrapper function for success."""
        mock_internal_indicator.return_value = MOCK_INDICATOR_DATA_RSI
        symbol = "AAPL"
        indicator = "RSI"
        period = 14
        result_str = calculate_technical_indicator(symbol, indicator, period)
        mock_internal_indicator.assert_called_once_with(symbol, indicator, period)
        assert "Technical Indicator: RSI (14-period) for Apple Inc. (AAPL)" in result_str
        assert "Current Value: 65.50" in result_str
        assert "INTERPRETATION:" in result_str
        assert "The RSI indicator is in the neutral zone..." in result_str
        assert "2024-04-24: 65.50" in result_str # Check recent value formatting

    @patch('tools.stock_tool.StockTool.get_technical_indicator')
    def test_calculate_technical_indicator_error(self, mock_internal_indicator):
        """Test calculate_technical_indicator wrapper when an error occurs."""
        error_message = "Indicator calculation failed"
        mock_internal_indicator.side_effect = Exception(error_message)
        symbol = "AAPL"
        indicator = "XYZ"
        period = 10
        result_str = calculate_technical_indicator(symbol, indicator, period)
        mock_internal_indicator.assert_called_once_with(symbol, indicator, period)
        assert f"Error calculating technical indicator: {error_message}" in result_str

    # Placeholder test
    def test_placeholder(self):
        assert True

# More tests will be added here for:
# - StockTool class initialization (if applicable)
# - get_stock_price function (mocking yfinance/API)
# - get_stock_info function (mocking yfinance/API)
# - search_stocks function (mocking yfinance/API)
# - Formatting functions
# - Error handling (invalid symbol, API down)
# - Helper functions 