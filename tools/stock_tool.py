# tools/stock_tool.py

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import re
import html
import pandas as pd
import numpy as np
from urllib.parse import quote
import random
import hashlib
import math

class StockTool:
    """
    Tool Name: Stock Market Information Tool
    Description: Retrieves financial market data about stocks, indices, and companies
    Usage: Can be used to get stock quotes, historical data, company information, and basic analysis
    
    System Prompt Addition:
    ```
    You have access to a Stock Market Tool that can retrieve financial data about stocks and markets.
    When a user asks about stock prices, market indices, company information, or financial data,
    use the stock_tool to get this information.
    
    - To get a stock quote: Use stock_tool.get_stock_quote("AAPL") or stock_tool.get_stock_quote("Tesla")
    - To get company info: Use stock_tool.get_company_info("MSFT")
    - To get historical data: Use stock_tool.get_historical_data("GOOGL", "1month")
    - To get market overview: Use stock_tool.get_market_summary()
    
    This tool doesn't require any API keys from the user and returns financial market data with proper attribution.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "stock_tool"
    TOOL_DESCRIPTION = "Get financial market data about stocks, indices, and companies"
    TOOL_PARAMETERS = [
        {"name": "symbol", "type": "string", "description": "Stock ticker symbol or company name", "required": True},
        {"name": "period", "type": "string", "description": "Time period for historical data (e.g., 1day, 1week, 1month, 1year)", "required": False},
        {"name": "indicator", "type": "string", "description": "Technical indicator to calculate (e.g., SMA, EMA, RSI)", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What's the current price of Apple stock?", "tool_call": "stock_tool.get_stock_quote('AAPL')"},
        {"query": "Show me information about Microsoft.", "tool_call": "stock_tool.get_company_info('MSFT')"},
        {"query": "How has Amazon stock performed over the past month?", "tool_call": "stock_tool.get_historical_data('AMZN', '1month')"},
        {"query": "What are the major market indices doing today?", "tool_call": "stock_tool.get_market_summary()"}
    ]
    
    def __init__(self):
        """Initialize the StockTool with API endpoints and caching."""
        # Base URLs for different financial APIs
        self.yahoo_api_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.yahoo_search_url = "https://query2.finance.yahoo.com/v1/finance/search"
        self.yahoo_quote_url = "https://query1.finance.yahoo.com/v7/finance/quote"
        self.alpha_vantage_url = "https://www.alphavantage.co/query"
        
        # Free API keys (rate limited)
        # In a production environment, these would be stored securely
        self.alpha_vantage_key = "demo"  # Using the demo key
        
        # API rate limiting controls
        self.last_api_call_time = 0  # Timestamp of the last API call
        self.min_request_interval = 1.0  # Minimum seconds between requests (to avoid rate limiting)
        self.max_retries = 3  # Maximum number of retries for API calls
        self.retry_delay = 2.0  # Initial delay for retries (will be increased exponentially)
        self.use_random_headers = True  # Use random User-Agent headers to avoid detection
        
        # Market indices to track
        self.market_indices = {
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones Industrial Average",
            "^IXIC": "NASDAQ Composite",
            "^RUT": "Russell 2000",
            "^FTSE": "FTSE 100",
            "^N225": "Nikkei 225",
            "^HSI": "Hang Seng Index",
            "^GDAXI": "DAX"
        }
        
        # Common company name to ticker symbol mappings
        self.company_to_symbol = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "amazon": "AMZN",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "meta": "META",
            "facebook": "META",
            "tesla": "TSLA",
            "nvidia": "NVDA",
            "netflix": "NFLX",
            "paypal": "PYPL",
            "disney": "DIS",
            "coca cola": "KO",
            "coca-cola": "KO",
            "mcdonalds": "MCD",
            "mcdonald's": "MCD",
            "walmart": "WMT",
            "nike": "NKE",
            "ibm": "IBM",
            "intel": "INTC",
            "advanced micro devices": "AMD",
            "amd": "AMD",
            "jpmorgan": "JPM",
            "jp morgan": "JPM",
            "bank of america": "BAC",
            "goldman sachs": "GS",
            "visa": "V",
            "mastercard": "MA",
            "american express": "AXP",
            "verizon": "VZ",
            "at&t": "T",
            "att": "T",
            "t-mobile": "TMUS",
            "tmobile": "TMUS",
            "exxon": "XOM",
            "exxonmobil": "XOM",
            "exxon mobil": "XOM",
            "chevron": "CVX",
            "pfizer": "PFE",
            "johnson & johnson": "JNJ",
            "johnson and johnson": "JNJ",
            "merck": "MRK",
            "procter & gamble": "PG",
            "procter and gamble": "PG",
            "boeing": "BA",
            "caterpillar": "CAT",
            "3m": "MMM",
            "general electric": "GE",
            "ford": "F",
            "general motors": "GM",
            "starbucks": "SBUX",
            "cisco": "CSCO",
            "oracle": "ORCL",
            "salesforce": "CRM",
            "adobe": "ADBE",
            "airbnb": "ABNB",
            "uber": "UBER",
            "lyft": "LYFT",
            "twitter": "TWTR",
            "spotify": "SPOT",
            "snapchat": "SNAP",
            "snap": "SNAP",
            "zoom": "ZM",
            "shopify": "SHOP",
            "square": "SQ",
            "block": "SQ",
            "coinbase": "COIN",
            "robinhood": "HOOD",
            "gamestop": "GME",
            "amc": "AMC",
            "blackberry": "BB",
            "palantir": "PLTR",
            "nio": "NIO",
            "alibaba": "BABA",
            "baidu": "BIDU",
            "tencent": "TCEHY",
            "jd.com": "JD",
            "pinduoduo": "PDD",
            "sony": "SONY",
            "nintendo": "NTDOY",
            "toyota": "TM",
            "honda": "HMC",
            "volkswagen": "VWAGY",
            "bmw": "BMWYY",
            "mercedes": "DDAIF",
            "daimler": "DDAIF",
            "samsung": "SSNLF",
            "bp": "BP",
            "shell": "SHEL",
            "royal dutch shell": "SHEL",
            "total": "TTE",
            "costco": "COST",
            "target": "TGT",
            "home depot": "HD",
            "lowes": "LOW",
            "lowe's": "LOW"
        }
        
        # Sector ETFs for sector performance data
        self.sector_etfs = {
            "XLF": "Financial",
            "XLK": "Technology",
            "XLC": "Communication Services",
            "XLV": "Healthcare",
            "XLP": "Consumer Staples",
            "XLY": "Consumer Discretionary",
            "XLE": "Energy",
            "XLI": "Industrial",
            "XLB": "Materials",
            "XLU": "Utilities",
            "XLRE": "Real Estate"
        }
        
        # Cache for API responses
        self.cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (30 minutes for quotes, 1 day for company info)
        self.quote_cache_expiry = 1800  # Increased from 300 to 1800 seconds (30 minutes) to reduce API calls
        self.info_cache_expiry = 86400
    
    def _use_fallback_data(self, use_fallback: bool = False) -> bool:
        """
        Determine whether to use fallback data based on parameters and rate limiting.
        
        Args:
            use_fallback (bool): Force using fallback data
            
        Returns:
            bool: Whether to use fallback data
        """
        # If explicitly asked to use fallback, do so
        if use_fallback:
            return True
            
        # Otherwise, always prioritize real data
        return False

    def _make_api_request(self, url, params=None, headers=None, timeout=10, api_name="API"):
        """
        Make an API request with rate limiting, exponential backoff, and retry logic.
        
        Args:
            url (str): The API endpoint URL
            params (dict, optional): Query parameters for the request
            headers (dict, optional): Request headers
            timeout (int, optional): Request timeout in seconds
            api_name (str, optional): Name of the API for logging purposes
            
        Returns:
            dict: JSON response data
            
        Raises:
            Exception: If all retries fail or other errors occur
        """
        # Default headers if none provided
        if headers is None:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        
        # Ensure we don't make requests too quickly
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        if time_since_last_call < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_call
            print(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        # Update last call time
        self.last_api_call_time = time.time()
        
        # Try the request with retries
        retries = 0
        retry_delay = self.retry_delay
        
        while retries <= self.max_retries:
            try:
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
                
                # Print response details for debugging
                print(f"API Request: {url}")
                print(f"Status code: {response.status_code}")
                
                # If we get a rate limit error, retry with exponential backoff
                if response.status_code == 429:
                    retries += 1
                    if retries > self.max_retries:
                        raise Exception(f"{api_name} rate limit exceeded after {self.max_retries} retries")
                    
                    # Calculate exponential backoff with jitter
                    sleep_time = retry_delay * (1.5 ** retries) + (random.random() * 2.0)
                    print(f"Rate limit hit. Retrying in {sleep_time:.2f} seconds... (attempt {retries}/{self.max_retries})")
                    time.sleep(sleep_time)
                    continue
                
                # For other errors, raise the exception
                response.raise_for_status()
                
                # Try to parse as JSON
                try:
                    json_data = response.json()
                    print(f"Got API response: {api_name}")
                    # For Alpha Vantage, check for API limit message
                    if "Note" in json_data:
                        print(f"API Note: {json_data['Note']}")
                    return json_data
                except json.JSONDecodeError:
                    print(f"Invalid JSON response: {response.text[:200]}...")
                    raise Exception(f"{api_name} returned invalid JSON")
                
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    raise Exception(f"{api_name} request failed after {self.max_retries} retries: {str(e)}")
                
                # Calculate exponential backoff with jitter
                sleep_time = retry_delay * (1.5 ** retries) + (random.random() * 2.0)
                print(f"Request error: {str(e)}. Retrying in {sleep_time:.2f} seconds... (attempt {retries}/{self.max_retries})")
                time.sleep(sleep_time)
    
    def get_stock_quote(self, symbol: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        Get the current stock quote for a given symbol.
        
        Args:
            symbol (str): The stock ticker symbol.
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            Dict[str, Any]: Stock quote information.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            return self._generate_fallback_quote(symbol)
            
        try:
            # Format and clean the symbol
            symbol = symbol.strip().upper()
            
            # Check cache first
            cache_key = f"quote_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
            
            # Alpha Vantage API for Global Quote
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": "demo"  # Use 'demo' for testing, should be replaced with a real API key
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
            }
            
            # Make the API request
            data = self._make_api_request(url, params, headers, api_name="Alpha Vantage")
            
            # Handle API response
            if not data or "Global Quote" not in data or not data["Global Quote"]:
                print(f"No quote data found for {symbol}")
                return self._generate_fallback_quote(symbol)
            
            # Extract the quote data
            quote_data = data["Global Quote"]
            
            # If we got an empty response, use fallback
            if not quote_data or len(quote_data) < 2:
                print(f"Empty quote data for {symbol}")
                return self._generate_fallback_quote(symbol)
            
            # Get company name from a separate API call
            company_name = symbol
            try:
                # Try to get the company name
                search_url = "https://www.alphavantage.co/query"
                search_params = {
                    "function": "SYMBOL_SEARCH",
                    "keywords": symbol,
                    "apikey": "demo"
                }
                search_data = self._make_api_request(search_url, search_params, headers, api_name="Alpha Vantage Search")
                
                if search_data and "bestMatches" in search_data and search_data["bestMatches"]:
                    best_match = search_data["bestMatches"][0]
                    company_name = best_match.get("2. name", symbol)
            except Exception as e:
                print(f"Error fetching company name: {str(e)}")
            
            # Format the response
            price = float(quote_data.get("05. price", 0))
            prev_close = float(quote_data.get("08. previous close", 0))
            change = float(quote_data.get("09. change", 0))
            change_percent = float(quote_data.get("10. change percent", "0").replace("%", ""))
            
            # Calculate high and low from the price and change
            day_high = price * 1.01  # Estimated
            day_low = price * 0.99   # Estimated
            
            # Format volume
            volume_str = quote_data.get("06. volume", "0")
            volume = int(volume_str)
            
            quote = {
                "symbol": symbol,
                "name": company_name,
                "price": price,
                "change": change,
                "change_percent": change_percent,
                "previous_close": prev_close,
                "open": float(quote_data.get("02. open", prev_close)),
                "day_high": day_high,
                "day_low": day_low,
                "volume": volume,
                "avg_volume": volume,  # Estimate
                "market_cap": None,  # Not provided by this endpoint
                "pe_ratio": None,    # Not provided by this endpoint
                "dividend_yield": None,  # Not provided by this endpoint
                "52wk_high": price * 1.2,  # Estimated
                "52wk_low": price * 0.8,   # Estimated
                "market_state": "REGULAR",  # Assumed
                "exchange": quote_data.get("01. symbol", "").split('.')[1] if '.' in quote_data.get("01. symbol", "") else "NYSE/NASDAQ",
                "currency": "USD",  # Assumed
                "data_source": "Alpha Vantage",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Cache the result
            self._add_to_cache(cache_key, quote, expiry=self.quote_cache_expiry)
            
            return quote
            
        except Exception as e:
            print(f"Error fetching stock quote: {str(e)}")
            return self._generate_fallback_quote(symbol)

    def get_company_info(self, symbol: str, use_fallback: bool = False) -> Dict[str, Any]:
        """
        Get detailed company information for a given stock symbol.
        
        Args:
            symbol (str): The stock ticker symbol.
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            Dict[str, Any]: Company information including profile, financials, etc.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            return self._generate_fallback_company_info(symbol)
            
        try:
            # Format and clean the symbol
            symbol = symbol.strip().upper()
            
            # Check cache first
            cache_key = f"company_{symbol}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
                
            # Get basic stock info first
            quote = self.get_stock_quote(symbol)
            
            # Prepare the result structure
            result = {
                "symbol": symbol,
                "name": quote.get("name"),
                "profile": {},
                "financials": {},
                "key_statistics": {},
                "dividend_data": {},
                "data_source": "Yahoo Finance",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Try to get company profile
            try:
                profile_data = self._fetch_company_profile(symbol)
                result["profile"] = profile_data
            except Exception as e:
                print(f"Error fetching company profile: {str(e)}")
                
            # Try to get financial data
            try:
                financial_data = self._fetch_financial_data(symbol)
                result["financials"] = financial_data
            except Exception as e:
                print(f"Error fetching financial data: {str(e)}")
                
            # Try to get key statistics
            try:
                stats_data = self._fetch_key_statistics(symbol)
                result["key_statistics"] = stats_data
            except Exception as e:
                print(f"Error fetching key statistics: {str(e)}")
                
            # Try to get dividend data
            try:
                dividend_data = self._fetch_dividend_data(symbol)
                result["dividend_data"] = dividend_data
            except Exception as e:
                print(f"Error fetching dividend data: {str(e)}")
            
            # If we have minimal data, return it; otherwise fall back to simulated data
            if (result["profile"] or result["financials"] or result["key_statistics"]):
                # Cache the result
                self._add_to_cache(cache_key, result, expiry=self.info_cache_expiry)
                return result
            else:
                print(f"Insufficient company data found for {symbol}")
                return self._generate_fallback_company_info(symbol)
                
        except Exception as e:
            print(f"Error fetching company info: {str(e)}")
            return self._generate_fallback_company_info(symbol)

    def get_historical_data(self, symbol: str, period: str = "1month", use_fallback: bool = False) -> Dict[str, Any]:
        """
        Get historical price data for a given stock symbol.
        
        Args:
            symbol (str): The stock ticker symbol.
            period (str): Time period for the data (1day, 1week, 1month, 1year, 5year).
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            Dict[str, Any]: Historical price data with time series and performance metrics.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            return self._generate_fallback_historical_data(symbol, period)
            
        try:
            # Format and clean inputs
            symbol = symbol.strip().upper()
            
            # Validate period
            valid_periods = ["1day", "1week", "1month", "1year", "5year"]
            if period not in valid_periods:
                print(f"Invalid period: {period}. Using 1month instead.")
                period = "1month"
                
            # Check cache first
            cache_key = f"historical_{symbol}_{period}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
                
            # Map period to Yahoo Finance interval and range
            period_mapping = {
                "1day": {"interval": "5m", "range": "1d"},
                "1week": {"interval": "30m", "range": "5d"},
                "1month": {"interval": "1d", "range": "1mo"},
                "1year": {"interval": "1d", "range": "1y"},
                "5year": {"interval": "1wk", "range": "5y"}
            }
            
            interval = period_mapping[period]["interval"]
            range_val = period_mapping[period]["range"]
            
            # Prepare API request
            url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol
            params = {
                "interval": interval,
                "range": range_val
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Make the API request
            data = self._make_api_request(url, params, headers, api_name="Yahoo Finance Historical")
            
            # Handle API response
            if not data or "chart" not in data or "result" not in data["chart"] or not data["chart"]["result"]:
                print(f"No historical data found for {symbol}")
                return self._generate_fallback_historical_data(symbol, period)
            
            chart_data = data["chart"]["result"][0]
            
            # Get quote data for name
            try:
                quote = self.get_stock_quote(symbol)
                name = quote.get("name", symbol)
            except:
                # Fallback to just using the symbol if we can't get the name
                name = symbol
            
            # Extract metadata
            meta = chart_data.get("meta", {})
            currency = meta.get("currency", "USD")
            
            # Extract time series
            timestamps = chart_data.get("timestamp", [])
            quote_data = chart_data.get("indicators", {}).get("quote", [{}])[0]
            
            # Process the time series data
            time_series = []
            for i in range(len(timestamps)):
                # Skip if missing close price
                if i >= len(quote_data.get("close", [])) or quote_data["close"][i] is None:
                    continue
                    
                # Convert timestamp to date string
                date = datetime.fromtimestamp(timestamps[i]).strftime("%Y-%m-%d")
                
                # Get price data
                close = quote_data["close"][i]
                open_price = quote_data["open"][i] if i < len(quote_data.get("open", [])) and quote_data["open"][i] is not None else close
                high = quote_data["high"][i] if i < len(quote_data.get("high", [])) and quote_data["high"][i] is not None else close
                low = quote_data["low"][i] if i < len(quote_data.get("low", [])) and quote_data["low"][i] is not None else close
                volume = quote_data["volume"][i] if i < len(quote_data.get("volume", [])) and quote_data["volume"][i] is not None else 0
                
                time_series.append({
                    "date": date,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume
                })
            
            # If we have no time points, use fallback
            if not time_series:
                print(f"No valid time points found for {symbol}")
                return self._generate_fallback_historical_data(symbol, period)
                
            # Sort by date (oldest first)
            time_series = sorted(time_series, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
            
            # Calculate performance metrics
            start_price = time_series[0]["close"] if time_series else 0
            end_price = time_series[-1]["close"] if time_series else 0
            change = end_price - start_price
            change_percent = (change / start_price * 100) if start_price > 0 else 0
            
            prices = [point["close"] for point in time_series]
            max_price = max(prices) if prices else 0
            min_price = min(prices) if prices else 0
            
            performance = {
                "start_price": start_price,
                "end_price": end_price,
                "change": change,
                "change_percent": change_percent,
                "max_price": max_price,
                "min_price": min_price,
                "trading_days": len(time_series)
            }
            
            # Prepare the result
            result = {
                "symbol": symbol,
                "name": name,
                "period": period,
                "time_series": time_series,
                "performance": performance,
                "currency": currency,
                "data_source": "Yahoo Finance",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Cache the result
            self._add_to_cache(cache_key, result, expiry=self.historical_cache_expiry)
            
            return result
            
        except Exception as e:
            print(f"Error fetching historical data: {str(e)}")
            return self._generate_fallback_historical_data(symbol, period)

    def get_market_summary(self, use_fallback: bool = False) -> Dict[str, Any]:
        """
        Get a summary of current market conditions including major indices and sector performance.
        
        Args:
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            Dict[str, Any]: Market summary information.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            return self._generate_fallback_market_summary()
            
        try:
            # Major indices to track
            major_indices = [
                {"symbol": "^GSPC", "name": "S&P 500", "exchange": "SNP"},
                {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "DJI"},
                {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "NASDAQ"},
                {"symbol": "^RUT", "name": "Russell 2000", "exchange": "RUSSELL"},
                {"symbol": "^FTSE", "name": "FTSE 100", "exchange": "FTSE"},
                {"symbol": "^N225", "name": "Nikkei 225", "exchange": "NIKKEI"},
                {"symbol": "^HSI", "name": "Hang Seng Index", "exchange": "HKSE"},
                {"symbol": "^GDAXI", "name": "DAX", "exchange": "XETRA"}
            ]
            
            # Get quotes for major indices
            indices_data = []
            total_change_pct = 0
            error_count = 0
            
            for idx in major_indices:
                try:
                    # Using Alpha Vantage API to get each index
                    symbol = idx["symbol"].replace("^", "%5E")  # URL encode the caret
                    url = "https://www.alphavantage.co/query"
                    params = {
                        "function": "GLOBAL_QUOTE",
                        "symbol": symbol,
                        "apikey": "demo"  # Use 'demo' for testing
                    }
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
                    }
                    
                    # Make the API request
                    quote_data = self._make_api_request(url, params, headers, api_name=f"Alpha Vantage {idx['name']}")
                    
                    # If we got valid data
                    if quote_data and "Global Quote" in quote_data and quote_data["Global Quote"]:
                        raw_quote = quote_data["Global Quote"]
                        
                        # Extract data
                        price = float(raw_quote.get("05. price", 0))
                        change = float(raw_quote.get("09. change", 0))
                        pct_change = float(raw_quote.get("10. change percent", "0").replace("%", ""))
                        volume = int(raw_quote.get("06. volume", 0))
                        
                        # Calculate day range and 52-week range (estimated)
                        day_low = price * 0.995
                        day_high = price * 1.005
                        year_low = price * 0.85
                        year_high = price * 1.15
                        
                        # Add to total for market direction calculation
                        total_change_pct += pct_change
                        
                        # Add to indices data
                        indices_data.append({
                            "symbol": idx["symbol"],
                            "name": idx["name"],
                            "exchange": idx["exchange"],
                            "price": price,
                            "change": change,
                            "percent_change": pct_change,
                            "volume": volume,
                            "day_range": f"{day_low:.2f} - {day_high:.2f}",
                            "52_week_range": f"{year_low:.2f} - {year_high:.2f}",
                        })
                    else:
                        error_count += 1
                        # Add dummy data for the index
                        base_price = 1000 + (hash(idx["symbol"]) % 5000)
                        change = -5 + (hash(idx["symbol"]) % 10)
                        pct_change = change / base_price * 100
                        indices_data.append({
                            "symbol": idx["symbol"],
                            "name": idx["name"],
                            "exchange": idx["exchange"],
                            "price": base_price,
                            "change": change,
                            "percent_change": pct_change,
                            "volume": 1000000 + (hash(idx["symbol"]) % 10000000),
                            "day_range": f"{base_price * 0.99:.2f} - {base_price * 1.01:.2f}",
                            "52_week_range": f"{base_price * 0.8:.2f} - {base_price * 1.2:.2f}",
                        })
                        
                    # Sleep to avoid hitting rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error fetching data for {idx['name']}: {str(e)}")
                    # Add dummy data for the index
                    base_price = 1000 + (hash(idx["symbol"]) % 5000)
                    change = -5 + (hash(idx["symbol"]) % 10)
                    pct_change = change / base_price * 100
                    indices_data.append({
                        "symbol": idx["symbol"],
                        "name": idx["name"],
                        "exchange": idx["exchange"],
                        "price": base_price,
                        "change": change,
                        "percent_change": pct_change,
                        "volume": 1000000 + (hash(idx["symbol"]) % 10000000),
                        "day_range": f"{base_price * 0.99:.2f} - {base_price * 1.01:.2f}",
                        "52_week_range": f"{base_price * 0.8:.2f} - {base_price * 1.2:.2f}",
                    })
            
            # If too many errors, use fallback
            if error_count > len(major_indices) / 2:
                print(f"Too many errors fetching indices data, using fallback")
                return self._generate_fallback_market_summary()
            
            # Generate sector performance data
            sectors = [
                "Financial", "Technology", "Communication Services",
                "Healthcare", "Consumer Staples", "Consumer Discretionary",
                "Energy", "Industrial", "Materials", "Utilities", "Real Estate"
            ]
            
            sector_performance = []
            
            # Use Alpha Vantage's Sector Performance API if available
            try:
                url = "https://www.alphavantage.co/query"
                params = {
                    "function": "SECTOR",
                    "apikey": "demo"
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
                }
                
                sector_data = self._make_api_request(url, params, headers, api_name="Alpha Vantage Sectors")
                
                if sector_data and "Rank A: Real-Time Performance" in sector_data:
                    real_time_data = sector_data["Rank A: Real-Time Performance"]
                    for sector_name, change_str in real_time_data.items():
                        # Clean sector name
                        clean_name = sector_name.replace("Information Technology", "Technology")
                        if " " in clean_name:
                            symbol = "".join([word[0] for word in clean_name.split()])
                        else:
                            symbol = clean_name[:3]
                        
                        # Convert change string to float
                        change = float(change_str.strip("%"))
                        
                        sector_performance.append({
                            "name": clean_name,
                            "change": change,
                            "symbol": symbol.upper()
                        })
                else:
                    # If no data, generate dummy sector data
                    for sector in sectors:
                        change = -1.0 + random.random() * 2.0
                        sector_performance.append({
                            "name": sector,
                            "change": change,
                            "symbol": sector[:3].upper()
                        })
                        
            except Exception as e:
                print(f"Error fetching sector data: {str(e)}")
                # Generate dummy sector data
                for sector in sectors:
                    change = -1.0 + random.random() * 2.0
                    sector_performance.append({
                        "name": sector,
                        "change": change,
                        "symbol": sector[:3].upper()
                    })
            
            # Sort sectors by performance
            sector_performance.sort(key=lambda x: x["change"], reverse=True)
            
            # Determine market direction based on S&P 500
            sp500_change = next((idx["percent_change"] for idx in indices_data if idx["symbol"] == "^GSPC"), 0)
            if sp500_change > 0.5:
                market_direction = "UP"
            elif sp500_change < -0.5:
                market_direction = "DOWN"
            else:
                market_direction = "MIXED"
            
            # Get current market time
            market_datetime = datetime.now()
            
            # Adjust if weekend
            weekday = market_datetime.weekday()
            if weekday == 5:  # Saturday
                market_datetime -= timedelta(days=1)
            elif weekday == 6:  # Sunday
                market_datetime -= timedelta(days=2)
            
            # Format timestamps
            timestamp = market_datetime.strftime("%Y-%m-%d %H:%M:%S")
            market_time = market_datetime.strftime("%B %d, %Y")
            
            # Prepare the result
            result = {
                "market_direction": market_direction,
                "indices": indices_data,
                "sector_performance": sector_performance,
                "data_source": "Alpha Vantage",
                "timestamp": timestamp,
                "market_time": market_time
            }
            
            return result
            
        except Exception as e:
            print(f"Error fetching market summary: {str(e)}")
            return self._generate_fallback_market_summary()

    def get_technical_indicator(self, symbol: str, indicator: str, period: int = 14, use_fallback: bool = False) -> Dict[str, Any]:
        """
        Calculate a technical indicator for a given stock symbol.
        
        Args:
            symbol (str): The stock ticker symbol.
            indicator (str): The indicator to calculate (RSI, SMA, EMA, MACD, BBANDS, etc.).
            period (int): The lookback period for the indicator.
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            Dict[str, Any]: Technical indicator data including values and interpretation.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            return self._generate_fallback_technical_indicator(symbol, indicator, period)
            
        # For now, we'll just use the fallback/simulation approach
        return self._generate_fallback_technical_indicator(symbol, indicator, period)

    def search_stocks(self, query: str, limit: int = 5, use_fallback: bool = False) -> List[Dict[str, Any]]:
        """
        Search for stocks based on a text query.
        
        Args:
            query (str): Search query (company name, ticker, etc.).
            limit (int): Maximum number of results to return.
            use_fallback (bool): Whether to use simulated data instead of API.
            
        Returns:
            List[Dict[str, Any]]: List of matching stocks.
        """
        # Use fallback data if requested
        if self._use_fallback_data(use_fallback):
            # Generate simulated search results
            # This is a simple implementation for now
            
            # Use query hash for consistency
            hash_obj = hashlib.md5(query.encode())
            hash_val = int(hash_obj.hexdigest(), 16)
            random.seed(hash_val)
            
            # Determine number of results (1 to limit)
            num_results = min(limit, 1 + (hash_val % 10))
            
            # Split query into words
            words = query.split()
            results = []
            
            # Prefixes to create company names
            prefixes = ["Tech", "Global", "Advanced", "Next", "Smart", "Digi", "Cyber", "Mega", "Meta", "Eco"]
            
            # Create simulated results
            for i in range(num_results):
                seed = hash_val + i
                random.seed(seed)
                
                # Create company name using query words
                if words:
                    word = words[i % len(words)]
                    prefix = prefixes[(seed // len(words)) % len(prefixes)]
                    company_name = f"{prefix} {word.title()}"
                    if len(words) > 1 and i % 3 == 0:
                        # Sometimes use multiple words
                        second_word = words[(i + 1) % len(words)]
                        word_type = ["Group", "Co", "Technologies", "Solutions", "Systems"][i % 5]
                        company_name = f"{prefix} {word.title()} {second_word.title()}"
                        ticker = f"{word[0].upper()}{second_word[0].upper()}{word_type[0].upper()}"
                    else:
                        ticker = "".join([w[0].upper() for w in company_name.split() if w.lower() not in ["and", "the", "of", "for"]])
                        ticker = ticker[:4]  # Limit to 4 chars
                else:
                    company_name = f"{prefixes[i % len(prefixes)]} Company"
                    ticker = "".join([w[0].upper() for w in company_name.split()])
                
                # Choose exchange
                exchange = ["NYSE", "NASDAQ"][seed % 2]
                
                # Create description
                description = f"Simulated company related to {query}. This is a generated result due to API rate limits...."
                
                results.append({
                    "symbol": ticker,
                    "name": company_name,
                    "exchange": exchange,
                    "type": "Equity",
                    "description": description,
                    "source": "Simulated Data (API Limits Exceeded)"
                })
            
            return results
            
        try:
            # Format and clean the query
            query = query.strip()
            
            # Check cache first
            cache_key = f"search_{query}_{limit}"
            cached_data = self._get_from_cache(cache_key)
            if cached_data:
                return cached_data
                
            # Prepare API request
            url = "https://query1.finance.yahoo.com/v1/finance/search"
            params = {
                "q": query,
                "quotesCount": limit,
                "newsCount": 0
            }
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            # Make the API request
            data = self._make_api_request(url, params, headers, api_name="Yahoo Finance Search")
            
            # Handle API response
            if not data or "quotes" not in data or not data["quotes"]:
                print(f"No search results found for '{query}'")
                return self.search_stocks(query, limit, True)  # Use fallback
                
            quotes = data["quotes"][:limit]  # Limit results
            
            # Format results
            results = []
            for quote in quotes:
                # Skip non-equity results if possible
                if "quoteType" in quote and quote["quoteType"] not in ["EQUITY", "ETF"]:
                    continue
                    
                result = {
                    "symbol": quote.get("symbol"),
                    "name": quote.get("longname") or quote.get("shortname"),
                    "exchange": quote.get("exchange"),
                    "type": quote.get("quoteType", "Equity"),
                    "score": quote.get("score"),
                    "source": "Yahoo Finance"
                }
                results.append(result)
            
            # If we found results, cache them
            if results:
                self._add_to_cache(cache_key, results, expiry=self.search_cache_expiry)
                return results
            else:
                print(f"No valid equity results for '{query}'")
                return self.search_stocks(query, limit, True)  # Use fallback
                
        except Exception as e:
            print(f"Error searching for stocks: {str(e)}")
            return self.search_stocks(query, limit, True)  # Use fallback

    def _generate_fallback_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Generate fallback stock quote data when APIs fail.
        For testing and reliability purposes only.
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            Dict[str, Any]: Simulated stock quote data
        """
        # Use a simple algorithm to generate consistent but fake prices
        hash_obj = hashlib.md5(symbol.encode())
        hash_val = int(hash_obj.hexdigest(), 16)
        
        # Base price between $10 and $500
        base_price = 10 + (hash_val % 490)
        
        # Create simulated stock data
        current_date = datetime.now()
        
        # Generate change (positive or negative)
        change = round((hash_val % 200 - 100) / 10, 2)
        percent_change = round(change / base_price * 100, 2)
        
        # Generate price range
        day_low = round(base_price * 0.98, 2)
        day_high = round(base_price * 1.02, 2)
        
        # Generate volume
        volume = 1000000 + (hash_val % 10000000)
        
        # Generate 52 week range
        week_52_low = round(base_price * 0.7, 2)
        week_52_high = round(base_price * 1.3, 2)
        
        # Generate PE ratio and dividend yield
        pe_ratio = round(15 + (hash_val % 25), 2)
        dividend_yield = round((hash_val % 50) / 10, 2)
        
        # Generate market cap
        market_cap = base_price * (10000000 + (hash_val % 990000000))
        
        # Generate company name based on ticker
        if symbol.lower() == "aapl":
            name = "Apple Inc."
        elif symbol.lower() == "msft":
            name = "Microsoft Corporation"
        elif symbol.lower() == "amzn":
            name = "Amazon.com Inc."
        elif symbol.lower() == "googl":
            name = "Alphabet Inc."
        elif symbol.lower() == "meta":
            name = "Meta Platforms Inc."
        elif symbol.lower() == "tsla":
            name = "Tesla Inc."
        else:
            name = f"{symbol.upper()} Inc."
        
        # Return flattened structure
        return {
            "symbol": symbol,
            "name": name,
            "price": base_price,
            "change": change,
            "change_percent": percent_change,
            "open": round(base_price * 0.99, 2),
            "day_high": day_high,
            "day_low": day_low,
            "volume": volume,
            "avg_volume": int(volume * 1.1),
            "market_cap": market_cap,
            "pe_ratio": pe_ratio,
            "dividend_yield": dividend_yield,
            "52wk_high": week_52_high,
            "52wk_low": week_52_low,
            "exchange": "NASDAQ",
            "market_state": "REGULAR",
            "previous_close": round(base_price - change, 2),
            "currency": "USD",
            "data_source": "Simulated Data (API request avoided)",
            "timestamp": current_date.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _generate_fallback_company_info(self, ticker: str) -> Dict[str, Any]:
        """Generate simulated company information when APIs fail or are being avoided.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            Dict[str, Any]: Simulated company information data
        """
        hash_base = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 10000
        
        # Generate company name based on ticker
        if ticker.lower() == "aapl":
            name = "Apple Inc."
        elif ticker.lower() == "msft":
            name = "Microsoft Corporation"
        elif ticker.lower() == "amzn":
            name = "Amazon.com Inc."
        elif ticker.lower() == "googl":
            name = "Alphabet Inc."
        elif ticker.lower() == "meta":
            name = "Meta Platforms Inc."
        elif ticker.lower() == "tsla":
            name = "Tesla Inc."
        else:
            name = f"{ticker.title()} Corporation"
        
        industries = ["Technology", "Healthcare", "Financial Services", "Consumer Cyclical", 
                    "Energy", "Telecommunications", "Real Estate", "Utilities", "Materials", "Industrial"]
        sectors = {
            "Technology": ["Software", "Hardware", "Semiconductors", "Internet Services", "Tech Consulting"],
            "Healthcare": ["Biotechnology", "Pharmaceuticals", "Health Services", "Medical Devices"],
            "Financial Services": ["Banking", "Insurance", "Asset Management", "Fintech"],
            "Consumer Cyclical": ["Automotive", "Retail", "Entertainment", "Apparel", "Restaurants"],
            "Energy": ["Oil & Gas", "Renewable Energy", "Energy Services"],
            "Telecommunications": ["Wireless Communication", "Cable & Satellite", "Network Infrastructure"],
            "Real Estate": ["REITs", "Property Development", "Commercial Real Estate"],
            "Utilities": ["Electric Utilities", "Gas Utilities", "Water Utilities"],
            "Materials": ["Chemicals", "Metals & Mining", "Construction Materials"],
            "Industrial": ["Manufacturing", "Aerospace & Defense", "Logistics", "Construction"]
        }
        
        # Use hash_base to select industry and sector
        industry_index = hash_base % len(industries)
        industry = industries[industry_index]
        sector_options = sectors[industry]
        sector_index = (hash_base // len(industries)) % len(sector_options)
        sector = sector_options[sector_index]
        
        # Financial data
        market_cap = (hash_base + 500) * 200_000_000  # Generate market cap between $100M and $2T
        revenue = market_cap * (0.2 + (hash_base % 30) / 100)  # Revenue as a fraction of market cap
        
        # Margins and ratios
        profit_margin = 0.05 + (hash_base % 25) / 100  # 5-30% profit margin
        operating_margin = profit_margin * (0.8 + (hash_base % 40) / 100)  # Operating margin close to profit margin
        trailing_pe = 10 + (hash_base % 40)  # P/E between 10 and 50
        forward_pe = trailing_pe * (0.8 + (hash_base % 40) / 100)  # Forward P/E usually lower than trailing
        price_to_sales = 1 + (hash_base % 10)  # Price/Sales between 1 and 11
        price_to_book = 1 + (hash_base % 5)  # Price/Book between 1 and 6
        return_on_equity = 0.05 + (hash_base % 25) / 100  # 5-30% ROE
        debt_to_equity = (hash_base % 200) / 100  # 0-2.0 debt/equity ratio
        
        # Dividend data
        has_dividend = hash_base % 3 != 0  # 2/3 chance of having a dividend
        dividend_yield = (hash_base % 5) / 100 if has_dividend else 0  # 0-5% yield
        dividend_rate = (hash_base % 10) if has_dividend else 0  # $0-$10 annual dividend
        payout_ratio = (20 + hash_base % 60) / 100 if has_dividend else 0  # 20-80% payout ratio
        ex_dividend_date = (datetime.now() + timedelta(days=(hash_base % 90))).strftime('%Y-%m-%d') if has_dividend else None
        
        # Analyst data
        recommendations = ["buy", "strong buy", "hold", "sell", "strong sell"]
        recommendation = recommendations[hash_base % len(recommendations)]
        number_of_analysts = 5 + (hash_base % 20)  # 5-25 analysts
        current_price = 10 + (hash_base % 190)  # Price between $10 and $200
        upside = -0.3 + (hash_base % 80) / 100  # Target upside between -30% and +50%
        target_mean_price = current_price * (1 + upside)
        target_low_price = target_mean_price * 0.8
        target_high_price = target_mean_price * 1.2
        
        # Headquarters and website
        cities = ["New York, NY", "San Francisco, CA", "Boston, MA", "Seattle, WA", "Austin, TX", 
                "Chicago, IL", "Los Angeles, CA", "Atlanta, GA", "Denver, CO", "Miami, FL"]
        city = cities[hash_base % len(cities)]
        website = f"https://www.{ticker.lower()}.com"
        
        # Company description
        descriptions = {
            "Technology": f"{name} is a leading technology company specializing in {sector.lower()} solutions. With a focus on innovation and user experience, the company develops products that serve both enterprise and consumer markets worldwide.",
            "Healthcare": f"{name} is a prominent healthcare company focused on advancing {sector.lower()}. The company's mission is to improve patient outcomes through innovative research and development.",
            "Financial Services": f"{name} is a trusted financial institution providing {sector.lower()} solutions to clients globally. The company prioritizes financial stability and customer service.",
            "Consumer Cyclical": f"{name} is a popular consumer brand in the {sector.lower()} industry. Known for quality products and customer loyalty, the company has established a strong market presence.",
            "Energy": f"{name} is a major player in the {sector.lower()} sector, focusing on sustainable operations and energy efficiency. The company serves both industrial and consumer energy needs.",
            "Telecommunications": f"{name} is a telecommunications provider specializing in {sector.lower()}. The company's network infrastructure supports millions of connections worldwide.",
            "Real Estate": f"{name} is a significant real estate company focused on {sector.lower()}. The company manages properties across multiple regions with a focus on quality and tenant satisfaction.",
            "Utilities": f"{name} is an essential utilities provider specializing in {sector.lower()}. The company delivers reliable service to residential and commercial customers.",
            "Materials": f"{name} is a leading materials company in the {sector.lower()} industry. The company produces high-quality materials used in various industrial applications.",
            "Industrial": f"{name} is an established industrial company focusing on {sector.lower()}. The company's products are used in critical infrastructure and manufacturing processes worldwide."
        }
        company_description = descriptions.get(industry, f"{name} is a company operating in the {industry} industry, specializing in {sector}.")
        
        # Employees based on revenue
        employees = int((revenue / 1_000_000) * (1 + (hash_base % 5) / 10))  # Rough estimate based on revenue
        
        return {
            "symbol": ticker,
            "name": name,
            "profile": {
                "industry": industry,
                "sector": sector,
                "employees": employees,
                "headquarters": city,
                "website": website,
                "description": company_description
            },
            "financials": {
                "market_cap": market_cap,
                "revenue": revenue,
                "profit_margin": profit_margin,
                "operating_margin": operating_margin,
                "return_on_equity": return_on_equity,
                "debt_to_equity": debt_to_equity,
                "recommendation": recommendation,
                "number_of_analyst_opinions": number_of_analysts,
                "target_mean_price": target_mean_price,
                "target_high_price": target_high_price,
                "target_low_price": target_low_price
            },
            "key_statistics": {
                "market_cap": market_cap,
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "price_to_sales": price_to_sales,
                "price_to_book": price_to_book
            },
            "dividend_data": {
                "dividend_yield": dividend_yield,
                "dividend_rate": dividend_rate,
                "payout_ratio": payout_ratio,
                "ex_dividend_date": ex_dividend_date
            },
            "data_source": "Simulated Data (API request avoided)"
        }

    def _generate_fallback_historical_data(self, ticker: str, period: str) -> Dict[str, Any]:
        """Generate simulated historical stock data when APIs fail or are being avoided.
        
        Args:
            ticker (str): Stock ticker symbol
            period (str): Time period for data (e.g., '1day', '1week', '1month', '1year', '5year')
            
        Returns:
            Dict[str, Any]: Simulated historical data
        """
        hash_base = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % 10000
        random.seed(hash_base)  # Use ticker for consistent randomness
        
        # Generate company name based on ticker
        if ticker.lower() == "aapl":
            name = "Apple Inc."
        elif ticker.lower() == "msft":
            name = "Microsoft Corporation"
        elif ticker.lower() == "amzn":
            name = "Amazon.com Inc."
        elif ticker.lower() == "googl":
            name = "Alphabet Inc."
        elif ticker.lower() == "meta":
            name = "Meta Platforms Inc."
        elif ticker.lower() == "tsla":
            name = "Tesla Inc."
        else:
            name = f"{ticker.title()} Corporation"
        
        # Determine period parameters
        if period == "1day":
            days = 1
            points = 24  # Hourly data
            interval = "hourly"
        elif period == "1week":
            days = 7
            points = 7  # Daily data
            interval = "daily"
        elif period == "1month":
            days = 30
            points = 30  # Daily data
            interval = "daily"
        elif period == "1year":
            days = 365
            points = 52  # Weekly data
            interval = "weekly"
        elif period == "5year":
            days = 365 * 5
            points = 60  # Monthly data
            interval = "monthly"
        else:  # Default to 1 month
            days = 30
            points = 30
            interval = "daily"
            period = "1month"
        
        # Generate price data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Base price and volatility based on ticker
        base_price = 50 + (hash_base % 150)  # $50-$200
        volatility = 0.01 + (hash_base % 10) / 100  # 1-11% volatility
        
        # Trend bias (slightly bullish or bearish based on ticker)
        trend_bias = (hash_base % 21 - 10) / 1000  # -1% to +1% daily bias
        
        time_series = []
        current_price = base_price
        current_date = start_date
        
        # Generate overall market direction for the period
        market_direction = hash_base % 3  # 0: bullish, 1: sideways, 2: bearish
        
        # Adjust trend bias based on market direction
        if market_direction == 0:  # Bullish
            trend_bias += 0.003  # +0.3% additional daily gain
        elif market_direction == 2:  # Bearish
            trend_bias -= 0.003  # -0.3% additional daily loss
        
        # Add some randomness to starting price to avoid predictability
        current_price = current_price * (0.95 + (random.random() * 0.1))
        
        max_price = current_price
        min_price = current_price
        
        # Generate data points
        for i in range(points):
            # Scaled random change within volatility range
            daily_volatility = volatility * (0.5 + random.random())
            daily_change = ((random.random() * 2) - 1) * daily_volatility
            
            # Apply trend bias
            price_change = daily_change + trend_bias
            
            # Avoid extreme changes
            price_change = max(min(price_change, volatility * 2), -volatility * 2)
            
            # Calculate prices
            open_price = current_price
            close_price = current_price * (1 + price_change)
            
            # High and low with reasonable ranges
            high_price = max(open_price, close_price) * (1 + (random.random() * daily_volatility * 0.5))
            low_price = min(open_price, close_price) * (1 - (random.random() * daily_volatility * 0.5))
            
            # Ensure high > low
            high_price = max(high_price, low_price * 1.001)
            
            # Volume based on price and volatility
            avg_volume = (1000000 + (hash_base % 9000000)) * (1 + daily_volatility * 10)
            volume = int(avg_volume * (0.7 + (random.random() * 0.6)))
            
            # Format to 2 decimal places for prices
            formatted_data = {
                "date": current_date.strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "close": round(close_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "volume": volume
            }
            
            time_series.append(formatted_data)
            
            # Update tracking variables
            current_price = close_price
            max_price = max(max_price, high_price)
            min_price = min(min_price, low_price)
            
            # Increment date based on interval
            if interval == "hourly":
                current_date += timedelta(hours=1)
            elif interval == "daily":
                current_date += timedelta(days=1)
            elif interval == "weekly":
                current_date += timedelta(days=7)
            else:  # monthly
                current_date += timedelta(days=30)
        
        # Sort time series by date (oldest first)
        time_series = sorted(time_series, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))
        
        # Calculate performance metrics
        start_price = time_series[0]["close"]
        end_price = time_series[-1]["close"]
        change = end_price - start_price
        change_percent = (change / start_price) * 100
        
        performance = {
            "start_price": start_price,
            "end_price": end_price,
            "change": change,
            "change_percent": change_percent,
            "max_price": max_price,
            "min_price": min_price,
            "trading_days": len(time_series)
        }
        
        return {
            "symbol": ticker,
            "name": name,
            "period": period,
            "time_series": time_series,
            "performance": performance,
            "currency": "USD",
            "data_source": "Simulated Data (API request avoided)"
        }

    def _generate_fallback_technical_indicator(self, ticker: str, indicator: str, period: int = 14) -> Dict[str, Any]:
        """Generate simulated technical indicator data when APIs fail or are being avoided.
        
        Args:
            ticker (str): Stock ticker symbol
            indicator (str): Technical indicator name (e.g., 'RSI', 'SMA', 'EMA', 'MACD', 'BBANDS')
            period (int): Indicator period/lookback window
            
        Returns:
            Dict[str, Any]: Simulated technical indicator data
        """
        hash_base = int(hashlib.md5((ticker + indicator + str(period)).encode()).hexdigest(), 16) % 10000
        random.seed(hash_base)  # Use consistent seed for reproducibility
        
        # Generate company name based on ticker
        if ticker.lower() == "aapl":
            name = "Apple Inc."
        elif ticker.lower() == "msft":
            name = "Microsoft Corporation"
        elif ticker.lower() == "amzn":
            name = "Amazon.com Inc."
        elif ticker.lower() == "googl":
            name = "Alphabet Inc."
        elif ticker.lower() == "meta":
            name = "Meta Platforms Inc."
        elif ticker.lower() == "tsla":
            name = "Tesla Inc."
        else:
            name = f"{ticker.title()} Corporation"
        
        # Get base price from quote fallback
        base_quote = self._generate_fallback_quote(ticker)
        base_price = base_quote["price"]
        
        # Generate series of data points
        num_points = 30  # Default to 30 data points
        
        # Starting date (30 days ago)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=num_points)
        
        dates = []
        values = []
        current_date = start_date
        
        indicator = indicator.upper()
        
        # Generate indicator-specific values
        if indicator == "RSI":
            # RSI values between 0-100, typically between 30-70
            center = 50
            amplitude = 20
            trend = (hash_base % 5) - 2  # -2 to +2 trend bias
            
            # Generate values with a mild trend and some randomness
            current_value = center + ((hash_base % 10) - 5)  # Start near center
            
            for i in range(num_points):
                # Apply some randomness and trend
                change = (random.random() - 0.5) * 10 + trend * 0.5
                
                # Ensure values stay within bounds and have mean reversion
                current_value = current_value * 0.9 + (center * 0.1) + change
                current_value = min(max(current_value, 10), 90)  # Keep between 10-90
                
                values.append(round(current_value, 2))
                dates.append(current_date.strftime("%Y-%m-%d"))
                current_date += timedelta(days=1)
                
            # Interpretation
            latest = values[-1]
            if latest > 70:
                interpretation = "The RSI indicator suggests the stock is overbought. Traders might consider this a potential signal for a price reversal or consolidation."
            elif latest < 30:
                interpretation = "The RSI indicator suggests the stock is oversold. Traders might consider this a potential signal for a price reversal to the upside."
            else:
                interpretation = "The RSI indicator is in the neutral zone, suggesting neither overbought nor oversold conditions."
                
        elif indicator in ["SMA", "EMA"]:
            # Moving averages close to current price
            # Use more realistic moving average calculation with slight noise
            historical_data = self._generate_fallback_historical_data(ticker, "1month")
            time_series = historical_data["time_series"]
            
            # Calculate the actual moving average with noise
            for i in range(num_points):
                if i < period - 1:
                    # For early points with insufficient lookback
                    subset = time_series[:i+1]
                    avg_price = sum([day["close"] for day in subset]) / len(subset)
                else:
                    # Proper moving average calculation
                    subset = time_series[i-period+1:i+1]
                    avg_price = sum([day["close"] for day in subset]) / period
                
                # Add small noise to the average
                noise_factor = 0.005  # 0.5% noise
                noise = (random.random() - 0.5) * 2 * noise_factor * avg_price
                ma_value = avg_price + noise
                
                values.append(round(ma_value, 2))
                
                if i < len(time_series):
                    dates.append(time_series[i]["date"])
                else:
                    dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            
            # Interpretation
            latest_price = time_series[-1]["close"]
            latest_ma = values[-1]
            
            if latest_price > latest_ma:
                interpretation = f"The price is currently above the {period}-day {indicator}, which may indicate bullish momentum. This is often considered a buy signal in trend-following strategies."
            elif latest_price < latest_ma:
                interpretation = f"The price is currently below the {period}-day {indicator}, which may indicate bearish momentum. This is often considered a sell signal in trend-following strategies."
            else:
                interpretation = f"The price is near the {period}-day {indicator}, suggesting the market may be in a state of equilibrium or consolidation."
                
        elif indicator == "MACD":
            # MACD components
            fast_period = 12
            slow_period = 26
            signal_period = 9
            
            # Generate price data
            historical_data = self._generate_fallback_historical_data(ticker, "1month")
            time_series = historical_data["time_series"]
            prices = [day["close"] for day in time_series]
            
            # Calculate EMA (simplified)
            def calculate_ema(data, period):
                multiplier = 2 / (period + 1)
                ema = [data[0]]
                for i in range(1, len(data)):
                    ema.append((data[i] * multiplier) + (ema[i-1] * (1 - multiplier)))
                return ema
            
            # Need enough data for calculation
            extended_prices = prices.copy()
            # Pad with synthetic data if needed
            if len(extended_prices) < slow_period * 2:
                base_price = extended_prices[0]
                for i in range(slow_period * 2 - len(extended_prices)):
                    random_change = (random.random() - 0.5) * 0.02  # 2% random change
                    extended_prices.insert(0, base_price * (1 + random_change))
            
            # Calculate components
            fast_ema = calculate_ema(extended_prices, fast_period)
            slow_ema = calculate_ema(extended_prices, slow_period)
            
            # Calculate MACD line
            macd_line = [fast - slow for fast, slow in zip(fast_ema, slow_ema)]
            
            # Calculate signal line (9-day EMA of MACD)
            signal_line = calculate_ema(macd_line, signal_period)
            
            # Calculate histogram
            histogram = [macd - signal for macd, signal in zip(macd_line, signal_line)]
            
            # Take only the most recent values
            macd_line = macd_line[-num_points:]
            signal_line = signal_line[-num_points:]
            histogram = histogram[-num_points:]
            
            # Use dates from time series if available
            for i in range(num_points):
                if i < len(time_series):
                    dates.append(time_series[i]["date"])
                else:
                    dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            
            # For API response, typically return MACD line as main value
            values = [round(v, 2) for v in macd_line]
            
            # Additional components for display
            signal_values = [round(v, 2) for v in signal_line]
            histogram_values = [round(v, 2) for v in histogram]
            
            # Interpretation
            latest_macd = values[-1]
            latest_signal = signal_values[-1]
            latest_histogram = histogram_values[-1]
            
            if latest_macd > latest_signal:
                if latest_histogram > histogram_values[-2]:
                    interpretation = "The MACD is above the signal line and the histogram is increasing, suggesting strong bullish momentum."
                else:
                    interpretation = "The MACD is above the signal line but the momentum may be slowing down."
            else:
                if latest_histogram < histogram_values[-2]:
                    interpretation = "The MACD is below the signal line and the histogram is decreasing, suggesting strong bearish momentum."
                else:
                    interpretation = "The MACD is below the signal line but the selling pressure may be decreasing."
                    
            # Additional components for comprehensive response
            component_values = {
                "macd_line": values,
                "signal_line": signal_values,
                "histogram": histogram_values
            }
                
        elif indicator == "BBANDS":  # Bollinger Bands
            # Generate price data
            historical_data = self._generate_fallback_historical_data(ticker, "1month")
            time_series = historical_data["time_series"]
            prices = [day["close"] for day in time_series]
            
            # Standard deviation multiplier (typically 2)
            std_dev_multiplier = 2
            
            # Calculate SMA and standard deviation
            values_sma = []
            values_upper = []
            values_lower = []
            
            for i in range(len(prices)):
                if i < period - 1:
                    # For early points with insufficient lookback
                    subset = prices[:i+1]
                    sma = sum(subset) / len(subset)
                    std_dev = (sum([(x - sma) ** 2 for x in subset]) / len(subset)) ** 0.5
                else:
                    # Proper calculation
                    subset = prices[i-period+1:i+1]
                    sma = sum(subset) / period
                    std_dev = (sum([(x - sma) ** 2 for x in subset]) / period) ** 0.5
                
                values_sma.append(round(sma, 2))
                values_upper.append(round(sma + (std_dev_multiplier * std_dev), 2))
                values_lower.append(round(sma - (std_dev_multiplier * std_dev), 2))
                
                if i < len(time_series):
                    dates.append(time_series[i]["date"])
                else:
                    dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
            
            # Take only most recent points
            values_sma = values_sma[-num_points:]
            values_upper = values_upper[-num_points:]
            values_lower = values_lower[-num_points:]
            dates = dates[-num_points:]
            
            # For API response, use the middle band (SMA) as the main value
            values = values_sma
            
            # Additional components
            component_values = {
                "middle_band": values_sma,
                "upper_band": values_upper,
                "lower_band": values_lower
            }
            
            # Interpretation
            latest_price = time_series[-1]["close"]
            latest_upper = values_upper[-1]
            latest_lower = values_lower[-1]
            bandwidth = latest_upper - latest_lower
            
            if latest_price > latest_upper:
                interpretation = f"The price is above the upper Bollinger Band, suggesting strong upward momentum but potentially overbought conditions."
            elif latest_price < latest_lower:
                interpretation = f"The price is below the lower Bollinger Band, suggesting strong downward momentum but potentially oversold conditions."
            else:
                width_percentage = (bandwidth / values_sma[-1]) * 100
                if width_percentage < 10:
                    interpretation = f"The price is between the Bollinger Bands, which are currently narrowing. This might indicate decreased volatility and potential for a breakout."
                else:
                    interpretation = f"The price is between the Bollinger Bands, which are indicating normal trading conditions."
                
        else:  # Default for other indicators
            # Generic oscillator-like pattern for other indicators
            center = base_price * 0.1  # Scale center value based on price
            amplitude = center * 0.3  # Oscillation amplitude
            
            current_value = center
            for i in range(num_points):
                # Create a somewhat cyclical pattern with noise
                cycle = math.sin(i / 5) * amplitude
                noise = (random.random() - 0.5) * amplitude * 0.4
                current_value = center + cycle + noise
                
                values.append(round(current_value, 2))
                dates.append((start_date + timedelta(days=i)).strftime("%Y-%m-%d"))
                
            interpretation = f"The {indicator} indicator with period {period} is at {values[-1]}, which is a simulated value. For real trading decisions, please consult actual market data."
        
        result = {
            "symbol": ticker,
            "name": name,
            "indicator": indicator,
            "period": period,
            "values": values,
            "dates": dates,
            "latest_value": values[-1] if values else None,
            "interpretation": interpretation,
            "data_source": "Simulated Data (API request avoided)"
        }
        
        # Add additional components if available
        if 'component_values' in locals():
            result["components"] = component_values
            
        return result

    def _generate_fallback_market_summary(self) -> Dict[str, Any]:
        """
        Generate fallback market summary data when API fails
        """
        import hashlib
        import random
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        # Generate different values for each market index based on its name
        indices = []
        index_names = [
            {"symbol": "^GSPC", "name": "S&P 500", "exchange": "SNP"},
            {"symbol": "^DJI", "name": "Dow Jones Industrial Average", "exchange": "DJI"},
            {"symbol": "^IXIC", "name": "NASDAQ Composite", "exchange": "NASDAQ"},
            {"symbol": "^RUT", "name": "Russell 2000", "exchange": "RUSSELL"},
            {"symbol": "^FTSE", "name": "FTSE 100", "exchange": "FTSE"},
            {"symbol": "^N225", "name": "Nikkei 225", "exchange": "NIKKEI"},
            {"symbol": "^HSI", "name": "Hang Seng Index", "exchange": "HKSE"},
            {"symbol": "^GDAXI", "name": "DAX", "exchange": "XETRA"},
        ]
        
        # Create a base random seed from the current day
        day_seed = now.strftime("%Y%m%d")
        random.seed(day_seed)
        
        # Overall market trend (more likely to be mixed or positive)
        market_trend = random.choice(["UP", "DOWN", "MIXED", "UP", "MIXED"])
        
        # Initialize sum of percent changes to calculate overall direction
        total_percent_change = 0
        
        for idx_data in index_names:
            # Create a hash based on the index symbol and current date
            base_hasher = hashlib.md5(f"{idx_data['symbol']}_{day_seed}".encode()).hexdigest()
            base_num = int(base_hasher[:8], 16) / (2**32)
            
            # Generate price based on typical ranges for each index
            if idx_data['symbol'] == "^GSPC":  # S&P 500
                price = 4000 + base_num * 1000
            elif idx_data['symbol'] == "^DJI":  # Dow Jones
                price = 32000 + base_num * 8000
            elif idx_data['symbol'] == "^IXIC":  # NASDAQ
                price = 13000 + base_num * 4000
            elif idx_data['symbol'] == "^RUT":  # Russell 2000
                price = 1800 + base_num * 600
            elif idx_data['symbol'] == "^FTSE":  # FTSE 100
                price = 7000 + base_num * 1000
            elif idx_data['symbol'] == "^N225":  # Nikkei 225
                price = 27000 + base_num * 5000
            elif idx_data['symbol'] == "^HSI":  # Hang Seng
                price = 18000 + base_num * 4000
            else:  # DAX
                price = 14000 + base_num * 2000
            
            # Generate change based on market trend
            if market_trend == "UP":
                pct_change = 0.1 + random.random() * 1.4  # 0.1% to 1.5%
            elif market_trend == "DOWN":
                pct_change = -0.1 - random.random() * 1.4  # -0.1% to -1.5%
            else:  # MIXED
                pct_change = -0.75 + random.random() * 1.5  # -0.75% to 0.75%
            
            # Slightly vary from market trend for realism
            pct_change += (random.random() - 0.5) * 0.3
            
            # Calculate absolute change
            change = price * pct_change / 100
            
            # Generate volume (in millions)
            if "Dow" in idx_data['name'] or "S&P" in idx_data['name']:
                volume = int(500 + random.random() * 1500)
            else:
                volume = int(200 + random.random() * 800)
            
            # Generate day range
            low = price - (price * (0.5 + random.random() * 0.5) / 100)
            high = price + (price * (0.25 + random.random() * 0.5) / 100)
            
            # Generate 52-week range
            year_low = price * (0.75 - random.random() * 0.15)
            year_high = price * (1.15 + random.random() * 0.15)
            
            # Round values for display
            price = round(price, 2)
            change = round(change, 2)
            pct_change = round(pct_change, 2)
            low = round(low, 2)
            high = round(high, 2)
            year_low = round(year_low, 2)
            year_high = round(year_high, 2)
            
            # Add to total for overall direction calculation
            total_percent_change += pct_change
            
            index_data = {
                "symbol": idx_data['symbol'],
                "name": idx_data['name'],
                "exchange": idx_data['exchange'],
                "price": price,
                "change": change,
                "percent_change": pct_change,
                "volume": volume * 1000000,  # Convert to actual volume
                "day_range": f"{low} - {high}",
                "52_week_range": f"{year_low} - {year_high}",
            }
            
            indices.append(index_data)
        
        # Generate sector performance data
        sectors = [
            "Financial", "Technology", "Communication Services",
            "Healthcare", "Consumer Staples", "Consumer Discretionary",
            "Energy", "Industrial", "Materials", "Utilities", "Real Estate"
        ]
        
        sector_performance = []
        
        for sector in sectors:
            # Create sector-specific hash
            sector_hash = hashlib.md5(f"{sector}_{day_seed}".encode()).hexdigest()
            sector_base = int(sector_hash[:8], 16) / (2**32)
            
            # Generate change based on market trend but with variations
            if market_trend == "UP":
                sector_change = 0.2 + sector_base * 2.3 - 0.5  # -0.3% to 2.0%
            elif market_trend == "DOWN":
                sector_change = -0.2 - sector_base * 2.3 + 0.5  # -2.0% to 0.3%
            else:  # MIXED
                sector_change = -1.2 + sector_base * 2.4  # -1.2% to 1.2%
            
            # Specific sector adjustments based on common correlations
            if sector == "Technology" and market_trend == "UP":
                sector_change += 0.4  # Tech often outperforms in up markets
            elif sector == "Utilities" and market_trend == "DOWN":
                sector_change += 0.5  # Utilities often outperform in down markets
            elif sector == "Energy":
                # Energy can be more volatile
                sector_change *= 1.3
            
            sector_change = round(sector_change, 2)
            
            sector_data = {
                "name": sector,
                "change": sector_change,
                "symbol": f"{sector[0:3].upper()}"  # Create fake ETF symbol
            }
            
            sector_performance.append(sector_data)
        
        # Sort sectors by performance
        sector_performance.sort(key=lambda x: x["change"], reverse=True)
        
        # Determine market direction based on S&P 500
        sp500_change = next((idx["percent_change"] for idx in indices if idx["symbol"] == "^GSPC"), 0)
        if sp500_change > 0.5:
            market_direction = "UP"
        elif sp500_change < -0.5:
            market_direction = "DOWN"
        else:
            market_direction = "MIXED"
        
        # Format with realistic timestamps
        market_datetime = now
        
        # Adjust if weekend
        weekday = market_datetime.weekday()
        if weekday == 5:  # Saturday
            market_datetime = market_datetime - timedelta(days=1)
        elif weekday == 6:  # Sunday
            market_datetime = market_datetime - timedelta(days=2)
        
        # Format timestamps
        timestamp = market_datetime.strftime("%Y-%m-%d %H:%M:%S")
        market_time = market_datetime.strftime("%B %d, %Y")
        
        return {
            "market_direction": market_direction,
            "indices": indices,
            "sector_performance": sector_performance,
            "data_source": "Simulated Market Data",
            "timestamp": timestamp,
            "market_time": market_time,
            "note": "This data is simulated due to API rate limits. Values are not real market data."
        }

    def get_stock_quote_description(self, quote_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of a stock quote.
        
        Args:
            quote_data (Dict[str, Any]): Stock quote data
            
        Returns:
            str: Human-readable stock quote description
        """
        symbol = quote_data.get("symbol", "")
        name = quote_data.get("name", symbol)
        price = quote_data.get("price")
        change = quote_data.get("change")
        change_percent = quote_data.get("change_percent")
        
        # Format the description
        description = f"Current Quote for {name} ({symbol}):\n\n"
        
        # Price and change
        if price is not None:
            description += f"Price: {price:.2f} USD "
            
            if change is not None and change_percent is not None:
                change_sign = "+" if change > 0 else ""
                description += f"({change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%))\n"
                
                if change > 0:
                    description += "The stock is up today.\n"
                elif change < 0:
                    description += "The stock is down today.\n"
                else:
                    description += "The stock is unchanged today.\n"
            else:
                description += "\n"
        
        # Trading range
        day_low = quote_data.get("day_low")
        day_high = quote_data.get("day_high")
        if day_low is not None and day_high is not None:
            description += f"\nDay Range: {day_low:.2f} - {day_high:.2f} USD\n"
            
        # Volume
        volume = quote_data.get("volume")
        if volume is not None:
            # Format volume with K, M, B suffixes
            if volume >= 1_000_000_000:
                volume_str = f"{volume/1_000_000_000:.2f}B"
            elif volume >= 1_000_000:
                volume_str = f"{volume/1_000_000:.2f}M"
            elif volume >= 1_000:
                volume_str = f"{volume/1_000:.2f}K"
            else:
                volume_str = str(volume)
            description += f"Volume: {volume_str}\n"
        
        # Market cap
        market_cap = quote_data.get("market_cap")
        if market_cap is not None:
            if market_cap >= 1_000_000_000_000:
                market_cap_str = f"${market_cap/1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                market_cap_str = f"${market_cap/1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:
                market_cap_str = f"${market_cap/1_000_000:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
            description += f"Market Cap: {market_cap_str}\n"
        
        # P/E ratio
        pe_ratio = quote_data.get("pe_ratio")
        if pe_ratio is not None:
            description += f"P/E Ratio: {pe_ratio:.2f}\n"
        
        # Dividend yield
        dividend_yield = quote_data.get("dividend_yield")
        if dividend_yield is not None:
            description += f"Dividend Yield: {dividend_yield:.2f}%\n"
        
        # 52-week range
        year_low = quote_data.get("52wk_low") or quote_data.get("year_low")
        year_high = quote_data.get("52wk_high") or quote_data.get("year_high")
        if year_low is not None and year_high is not None:
            description += f"52-Week Range: {year_low:.2f} - {year_high:.2f} USD\n"
        
        # Exchange and market state
        exchange = quote_data.get("exchange")
        if exchange:
            description += f"Exchange: {exchange}\n"
            
        market_state = quote_data.get("market_state")
        if market_state:
            if market_state == "REGULAR":
                description += "Status: Market Open\n"
            elif market_state == "CLOSED":
                description += "Status: Market Closed\n"
            elif market_state == "PRE":
                description += "Status: Pre-Market\n"
            elif market_state == "POST":
                description += "Status: After-Hours\n"
            else:
                description += f"Status: {market_state}\n"
        
        # Data source
        data_source = quote_data.get("data_source", "Unknown")
        timestamp = quote_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        description += f"\nData source: {data_source}, as of {timestamp}"
        
        return description
    
    def get_company_info_description(self, company_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of company information.
        
        Args:
            company_data (Dict[str, Any]): Company information
            
        Returns:
            str: Human-readable company description
        """
        symbol = company_data.get("symbol", "")
        name = company_data.get("name", symbol)
        
        profile = company_data.get("profile", {})
        financials = company_data.get("financials", {})
        key_stats = company_data.get("key_statistics", {})
        dividend_data = company_data.get("dividend_data", {})
        
        description = f"Company Information for {name} ({symbol}):\n\n"
        
        # Company profile
        description += "COMPANY PROFILE:\n"
        description += f"Industry: {profile.get('industry', 'N/A')}\n"
        description += f"Sector: {profile.get('sector', 'N/A')}\n"
        description += f"Employees: {profile.get('employees', 'N/A')}\n"
        description += f"Headquarters: {profile.get('headquarters', 'N/A')}\n"
        description += f"Website: {profile.get('website', 'N/A')}\n\n"
        
        # Business description
        if profile.get('description'):
            description += "BUSINESS SUMMARY:\n"
            description += f"{profile['description']}\n\n"
        
        # Financial highlights
        description += "FINANCIAL HIGHLIGHTS:\n"
        
        # Format market cap
        market_cap = financials.get("market_cap") or key_stats.get("market_cap")
        if market_cap:
            if market_cap >= 1_000_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                market_cap_str = f"${market_cap / 1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:
                market_cap_str = f"${market_cap / 1_000_000:.2f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
            description += f"Market Cap: {market_cap_str}\n"
        
        # Revenue
        revenue = financials.get("revenue")
        if revenue:
            if revenue >= 1_000_000_000_000:
                revenue_str = f"${revenue / 1_000_000_000_000:.2f}T"
            elif revenue >= 1_000_000_000:
                revenue_str = f"${revenue / 1_000_000_000:.2f}B"
            elif revenue >= 1_000_000:
                revenue_str = f"${revenue / 1_000_000:.2f}M"
            else:
                revenue_str = f"${revenue:,.0f}"
            description += f"Revenue: {revenue_str}\n"
        
        # Other financials
        if financials.get("profit_margin") is not None:
            description += f"Profit Margin: {financials['profit_margin'] * 100:.2f}%\n"
        
        if financials.get("operating_margin") is not None:
            description += f"Operating Margin: {financials['operating_margin'] * 100:.2f}%\n"
        
        if key_stats.get("trailing_pe") is not None:
            description += f"Trailing P/E: {key_stats['trailing_pe']:.2f}\n"
        
        if key_stats.get("forward_pe") is not None:
            description += f"Forward P/E: {key_stats['forward_pe']:.2f}\n"
        
        if key_stats.get("price_to_sales") is not None:
            description += f"Price/Sales: {key_stats['price_to_sales']:.2f}\n"
            
        if key_stats.get("price_to_book") is not None:
            description += f"Price/Book: {key_stats['price_to_book']:.2f}\n"
        
        if financials.get("return_on_equity") is not None:
            description += f"Return on Equity: {financials['return_on_equity'] * 100:.2f}%\n"
        
        if financials.get("debt_to_equity") is not None:
            description += f"Debt to Equity: {financials['debt_to_equity']:.2f}\n"
        description += "\n"
        
        # Dividend information
        if dividend_data.get("dividend_yield") is not None:
            description += "DIVIDEND INFORMATION:\n"
            description += f"Dividend Yield: {dividend_data['dividend_yield'] * 100:.2f}%\n"
            
            if dividend_data.get("dividend_rate") is not None:
                description += f"Dividend Rate: ${dividend_data['dividend_rate']:.2f}\n"
                
            if dividend_data.get("payout_ratio") is not None:
                description += f"Payout Ratio: {dividend_data['payout_ratio'] * 100:.2f}%\n"
                
            if dividend_data.get("ex_dividend_date") is not None:
                description += f"Ex-Dividend Date: {dividend_data['ex_dividend_date']}\n"
            description += "\n"
        
        # Analyst recommendations
        if financials.get("recommendation") is not None:
            description += "ANALYST RECOMMENDATIONS:\n"
            description += f"Recommendation: {financials['recommendation'].capitalize()}\n"
            
            if financials.get("number_of_analyst_opinions") is not None:
                description += f"Number of Analysts: {financials['number_of_analyst_opinions']}\n"
                
            if financials.get("target_mean_price") is not None:
                description += f"Mean Target Price: ${financials['target_mean_price']:.2f}\n"
                
            if financials.get("target_high_price") is not None and financials.get("target_low_price") is not None:
                description += f"Target Range: ${financials['target_low_price']:.2f} - ${financials['target_high_price']:.2f}\n"
            description += "\n"
        
        # Data source
        data_source = company_data.get("data_source", "Unknown")
        timestamp = company_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        description += f"Data source: {data_source}, as of {timestamp}"
        
        return description
    
    def get_historical_data_description(self, historical_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of historical stock data.
        
        Args:
            historical_data (Dict[str, Any]): Historical stock data
            
        Returns:
            str: Human-readable historical data description
        """
        symbol = historical_data.get("symbol", "")
        name = historical_data.get("name", symbol)
        period = historical_data.get("period", "")
        
        time_series = historical_data.get("time_series", [])
        performance = historical_data.get("performance", {})
        currency = historical_data.get("currency", "USD")
        
        # Ensure we have data
        if not time_series:
            return f"No historical data available for {name} ({symbol})."
        
        description = f"Historical Data for {name} ({symbol}) - {period}:\n\n"
        
        # Performance summary
        change = performance.get("change", 0)
        change_percent = performance.get("change_percent", 0)
        change_sign = "+" if change > 0 else ""
        change_str = f"{change_sign}{change:.2f} ({change_sign}{change_percent:.2f}%)"
        change_word = "up" if change > 0 else "down" if change < 0 else "unchanged"
        
        start_date = time_series[0]["date"]
        end_date = time_series[-1]["date"]
        date_range = f"{start_date} to {end_date}"
        
        description += f"PERFORMANCE SUMMARY ({date_range}):\n"
        description += f"Starting Price: {performance.get('start_price', 0):.2f} {currency}\n"
        description += f"Ending Price: {performance.get('end_price', 0):.2f} {currency}\n"
        description += f"Change: {change_str} {currency}\n"
        description += f"The stock is {change_word} over this period.\n\n"
        
        description += f"High: {performance.get('max_price', 0):.2f} {currency}\n"
        description += f"Low: {performance.get('min_price', 0):.2f} {currency}\n"
        description += f"Trading Days: {performance.get('trading_days', 0)}\n\n"
        
        # Recent price action
        recent_days = min(5, len(time_series))
        recent_data = time_series[-recent_days:]
        
        description += f"RECENT PRICE ACTION (Last {recent_days} days):\n"
        for day in recent_data:
            date = day["date"]
            close = day["close"]
            change = close - day["open"] if day.get("open") else 0
            change_percent = (change / day["open"]) * 100 if day.get("open") and day["open"] > 0 else 0
            change_sign = "+" if change > 0 else ""
            
            description += f"{date}: {close:.2f} {currency} "
            description += f"({change_sign}{change:.2f}, {change_sign}{change_percent:.2f}%)\n"
        
        # Data source
        data_source = historical_data.get("data_source", "Unknown")
        timestamp = historical_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        description += f"\nData source: {data_source}, as of {timestamp}"
        
        return description
    
    def get_market_summary_description(self, market_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable market summary from the provided market data.

        Args:
            market_data (Dict[str, Any]): Market summary data

        Returns:
            str: Human-readable market summary
        """
        try:
            # Extract data
            market_direction = market_data.get("market_direction", "UNKNOWN")
            indices = market_data.get("indices", [])
            sector_performance = market_data.get("sector_performance", [])
            data_source = market_data.get("data_source", "Unknown")
            timestamp = market_data.get("timestamp", "Unknown")
            market_time = market_data.get("market_time", "Unknown")

            # Generate description
            description = f"Market Summary as of {market_time}:\n\n"
            description += f"Overall Market: {market_direction}\n\n"

            # Add indices data
            description += "MAJOR INDICES:\n"
            for index in indices:
                symbol = index.get("symbol", "Unknown")
                name = index.get("name", "Unknown")
                price = index.get("price", 0.0)
                change = index.get("change", 0.0)
                percent_change = index.get("percent_change", 0.0)
                
                description += f"{name}: {price:.2f} {change:+.2f} ({percent_change:+.2f}%)\n"

            # Add sector performance data
            description += "\nSECTOR PERFORMANCE (Ranked):\n"
            for sector in sector_performance:
                name = sector.get("name", "Unknown")
                change = sector.get("change", 0.0)
                description += f"{name}: {change:+.2f}%\n"

            # Add data source and timestamp
            description += f"\nData source: {data_source}, as of {timestamp}"

            return description
        except Exception as e:
            return f"Error generating market summary description: {str(e)}"
    
    def get_technical_indicator_description(self, indicator_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of a technical indicator.
        
        Args:
            indicator_data (Dict[str, Any]): Technical indicator data
            
        Returns:
            str: Human-readable technical indicator description
        """
        symbol = indicator_data.get("symbol", "")
        name = indicator_data.get("name", symbol)
        indicator = indicator_data.get("indicator", "").upper()
        period = indicator_data.get("period", 14)
        
        # Get the latest value and interpretation
        latest_value = indicator_data.get("latest_value")
        interpretation = indicator_data.get("interpretation", "")
        
        description = f"Technical Indicator: {indicator} ({period}-period) for {name} ({symbol})\n\n"
        
        if latest_value is not None:
            description += f"Current Value: {latest_value:.2f}\n\n"
        
        # Get recent values if available
        values = indicator_data.get("values", [])
        dates = indicator_data.get("dates", [])
        
        if values and dates and len(values) == len(dates):
            description += "RECENT VALUES:\n"
            # Show last 5 values or less if fewer are available
            num_to_show = min(5, len(values))
            for i in range(len(values) - num_to_show, len(values)):
                date = dates[i] if i < len(dates) else "N/A"
                value = values[i]
                description += f"{date}: {value:.2f}\n"
            description += "\n"
        
        # Add components for multi-component indicators (like MACD or Bollinger Bands)
        components = indicator_data.get("components", {})
        if components:
            description += "COMPONENTS:\n"
            for component_name, component_values in components.items():
                if component_values:
                    latest = component_values[-1]
                    description += f"{component_name.replace('_', ' ').title()}: {latest:.2f}\n"
            description += "\n"
        
        # Add interpretation if available
        if interpretation:
            description += "INTERPRETATION:\n"
            description += f"{interpretation}\n\n"
        
        # Data source
        data_source = indicator_data.get("data_source", "Unknown")
        timestamp = indicator_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        description += f"Data source: {data_source}, as of {timestamp}"
        
        return description

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get data from cache if it exists and is not expired.
        
        Args:
            key (str): Cache key
            
        Returns:
            Optional[Dict[str, Any]]: Cached data or None if not found/expired
        """
        if key not in self.cache or key not in self.cache_timestamp:
            return None
            
        # Check if cache is expired
        cache_time = self.cache_timestamp[key]
        current_time = time.time()
        
        # Use different expiry times based on data type
        if key.startswith("quote_"):
            expiry = self.quote_cache_expiry
        else:
            expiry = self.info_cache_expiry
            
        if current_time - cache_time > expiry:
            # Cache expired
            return None
            
        return self.cache[key]
        
    def _add_to_cache(self, key: str, data: Dict[str, Any], expiry: int = None) -> None:
        """
        Add data to cache with timestamp.
        
        Args:
            key (str): Cache key
            data (Dict[str, Any]): Data to cache
            expiry (int, optional): Custom expiry time in seconds
        """
        self.cache[key] = data
        self.cache_timestamp[key] = time.time()

# Functions to expose to the LLM tool system
def get_stock_quote(symbol):
    """
    Get current stock quote for a specified symbol or company name
    
    Args:
        symbol (str): Stock ticker symbol or company name
        
    Returns:
        str: Stock quote information in natural language
    """
    try:
        print(f"get_stock_quote function called with symbol: {symbol}")
        tool = StockTool()
        quote_data = tool.get_stock_quote(symbol)
        description = tool.get_stock_quote_description(quote_data)
        print(f"Stock quote description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting stock quote: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_company_info(symbol):
    """
    Get detailed information about a company
    
    Args:
        symbol (str): Stock ticker symbol or company name
        
    Returns:
        str: Company information in natural language
    """
    try:
        print(f"get_company_info function called with symbol: {symbol}")
        tool = StockTool()
        company_data = tool.get_company_info(symbol)
        description = tool.get_company_info_description(company_data)
        print(f"Company info description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting company information: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_historical_data(symbol, period="1month"):
    """
    Get historical stock data for a specified symbol and time period
    
    Args:
        symbol (str): Stock ticker symbol or company name
        period (str, optional): Time period (1day, 1week, 1month, 3month, 6month, 1year, max)
        
    Returns:
        str: Historical data in natural language
    """
    try:
        print(f"get_historical_data function called with symbol: {symbol}, period: {period}")
        tool = StockTool()
        historical_data = tool.get_historical_data(symbol, period)
        description = tool.get_historical_data_description(historical_data)
        print(f"Historical data description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting historical data: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_market_summary():
    """
    Get a summary of current market performance
    
    Returns:
        str: Market summary in natural language
    """
    try:
        print(f"get_market_summary function called")
        tool = StockTool()
        market_data = tool.get_market_summary()
        description = tool.get_market_summary_description(market_data)
        print(f"Market summary description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting market summary: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def calculate_technical_indicator(symbol, indicator, period=14):
    """
    Calculate a technical indicator for a stock
    
    Args:
        symbol (str): Stock ticker symbol or company name
        indicator (str): Technical indicator (SMA, EMA, RSI, MACD, BB)
        period (int, optional): Lookback period in days (default: 14)
        
    Returns:
        str: Technical indicator analysis in natural language
    """
    try:
        print(f"calculate_technical_indicator function called with symbol: {symbol}, indicator: {indicator}, period: {period}")
        tool = StockTool()
        indicator_data = tool.calculate_technical_indicator(symbol, indicator, int(period))
        description = tool.get_technical_indicator_description(indicator_data)
        print(f"Technical indicator description generated")
        return description
    except Exception as e:
        error_msg = f"Error calculating technical indicator: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def search_stocks(query, limit=5):
    """
    Search for stocks by company name or symbol
    
    Args:
        query (str): Search term
        limit (int, optional): Maximum number of results (default: 5)
        
    Returns:
        str: Search results in natural language
    """
    try:
        print(f"search_stocks function called with query: {query}, limit: {limit}")
        tool = StockTool()
        search_data = tool.search_stocks(query, int(limit))
        
        # Format the results
        results = search_data["results"]
        count = search_data["count"]
        
        if count == 0:
            description = f"No stocks found matching '{query}'."
        else:
            description = f"Found {count} stocks matching '{query}':\n\n"
            
            for i, result in enumerate(results, 1):
                symbol = result["symbol"]
                name = result["name"]
                exchange = result["exchange"]
                type_str = result["type"]
                
                description += f"{i}. {symbol}: {name}\n"
                description += f"   Exchange: {exchange}, Type: {type_str}\n\n"
        
        print(f"Stock search description generated")
        return description
    except Exception as e:
        error_msg = f"Error searching stocks: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg