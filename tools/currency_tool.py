# tools/currency_tool.py

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

class CurrencyTool:
    """
    Tool Name: Currency Conversion Tool
    Description: Converts amounts between different currencies using real-time exchange rates
    Usage: Can be used to convert amounts between any supported currency pairs
    
    System Prompt Addition:
    ```
    You have access to a Currency Tool that can convert amounts between different currencies
    using up-to-date exchange rates. When a user asks about currency conversion, exchange rates,
    or the value of an amount in another currency, use the currency_tool to get this information.
    
    - To convert currency: Use currency_tool.convert_currency(amount, from_currency, to_currency)
    - To get exchange rates: Use currency_tool.get_exchange_rates(base_currency)
    
    This tool doesn't require any API keys and returns detailed currency conversion information.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "currency_tool"
    TOOL_DESCRIPTION = "Convert amounts between different currencies using real-time exchange rates"
    TOOL_PARAMETERS = [
        {"name": "amount", "type": "number", "description": "Amount to convert", "required": True},
        {"name": "from_currency", "type": "string", "description": "Source currency code (e.g., USD, EUR)", "required": True},
        {"name": "to_currency", "type": "string", "description": "Target currency code (e.g., JPY, GBP)", "required": True}
    ]
    TOOL_EXAMPLES = [
        {"query": "Convert 100 USD to EUR", "tool_call": "currency_tool.convert_currency(100, 'USD', 'EUR')"},
        {"query": "How much is 50 euros in Japanese yen?", "tool_call": "currency_tool.convert_currency(50, 'EUR', 'JPY')"},
        {"query": "Exchange rate from British Pounds to Canadian Dollars", "tool_call": "currency_tool.convert_currency(1, 'GBP', 'CAD')"},
        {"query": "Convert 1000 руб to USD", "tool_call": "currency_tool.convert_currency(1000, 'RUB', 'USD')"}
    ]
    
    def __init__(self):
        """Initialize the CurrencyTool with free API endpoints."""
        # Using ExchangeRate-API's free endpoint
        self.exchange_rates_url = "https://open.er-api.com/v6/latest/"
        # Secondary backup API
        self.backup_api_url = "https://api.exchangerate.host/latest"
        # Cache for exchange rates to minimize API calls
        self.exchange_rates_cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (1 hour)
        self.cache_expiry = 3600
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Convert an amount from one currency to another.
        
        Args:
            amount (float): The amount to convert
            from_currency (str): Source currency code (e.g., USD, EUR)
            to_currency (str): Target currency code (e.g., JPY, GBP)
        
        Returns:
            Dict[str, Any]: Conversion result with details
            
        Raises:
            Exception: If the API request fails or currencies are invalid
        """
        # Ensure amount is a float
        try:
            amount_float = float(amount)
        except (ValueError, TypeError):
            raise Exception(f"Invalid amount provided: '{amount}'. Amount must be a number.")
        
        print(f"Converting {amount_float} {from_currency} to {to_currency}")
        
        # Standardize currency codes
        from_currency = self._standardize_currency_code(from_currency)
        to_currency = self._standardize_currency_code(to_currency)
        
        # Validate currency codes before proceeding
        if len(from_currency) != 3 or not from_currency.isalpha():
            raise Exception(f"Currency '{from_currency}' is not supported")
        if len(to_currency) != 3 or not to_currency.isalpha():
            raise Exception(f"Currency '{to_currency}' is not supported")

        # If converting to the same currency, short-circuit the call
        if from_currency == to_currency:
            return {
                "query": {
                    "amount": amount_float,
                    "from": from_currency,
                    "to": to_currency,
                    "timestamp": datetime.now().isoformat()
                },
                "result": {
                    "amount": amount_float,
                    "formatted": f"{amount_float:.2f} {to_currency}"
                },
                "info": {
                    "rate": 1.0,
                    "timestamp": datetime.now().isoformat(),
                    "inverse_rate": 1.0
                }
            }

        try:
            # Get the exchange rates with the source currency as base
            rates = self._get_exchange_rates(from_currency)
        except Exception as e:
            # Wrap lower-level exceptions in a consistent, test-friendly message
            raise Exception(f"Error in currency conversion: {e}") from e

        # Check if the target currency is supported
        if to_currency not in rates:
            raise Exception(f"Currency '{to_currency}' is not supported")

        # Perform the conversion
        converted_amount = amount_float * rates[to_currency]

        # Format the response
        result = {
            "query": {
                "amount": amount_float,
                "from": from_currency,
                "to": to_currency,
                "timestamp": datetime.now().isoformat()
            },
            "result": {
                "amount": converted_amount,
                "formatted": f"{converted_amount:.2f} {to_currency}"
            },
            "info": {
                "rate": rates[to_currency],
                "timestamp": datetime.now().isoformat(),
                "inverse_rate": 1 / rates[to_currency]
            }
        }

        return result
    
    def get_exchange_rates(self, base_currency: str) -> Dict[str, Any]:
        """
        Get current exchange rates for a base currency.
        
        Args:
            base_currency (str): Base currency code (e.g., USD, EUR)
        
        Returns:
            Dict[str, Any]: Exchange rates with details
            
        Raises:
            Exception: If the API request fails or currency is invalid
        """
        print(f"Getting exchange rates for base currency: {base_currency}")
        
        # Standardize currency code
        base_currency = self._standardize_currency_code(base_currency)
        
        # Get the exchange rates
        rates = self._get_exchange_rates(base_currency)
        
        # Format the response
        result = {
            "base_currency": base_currency,
            "rates": rates,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
    
    def _standardize_currency_code(self, currency: str) -> str:
        """
        Standardize currency code format (uppercase, handle common variations).
        
        Args:
            currency (str): Currency code or common name
        
        Returns:
            str: Standardized 3-letter currency code
        """
        # Convert to uppercase
        currency = currency.upper().strip()
        
        # Handle common variations
        currency_mapping = {
            "DOLLAR": "USD",
            "DOLLARS": "USD",
            "US": "USD",
            "EURO": "EUR",
            "EUROS": "EUR",
            "POUND": "GBP",
            "POUNDS": "GBP",
            "STERLING": "GBP",
            "YEN": "JPY",
            "YUAN": "CNY",
            "RENMINBI": "CNY",
            "FRANC": "CHF",
            "FRANCS": "CHF",
            "RUBLE": "RUB",
            "RUBLES": "RUB",
            "РУБ": "RUB",
            "РУБЛЬ": "RUB",
            "РУБЛЯ": "RUB",
            "РУБЛЕЙ": "RUB",
            "CANADIAN": "CAD",
            "CAD$": "CAD",
            "AUD$": "AUD",
            "AUSTRALIAN": "AUD",
            "CRYPTO": "BTC",
            "BITCOIN": "BTC"
        }
        
        # Check if the currency is in our mapping
        if currency in currency_mapping:
            return currency_mapping[currency]
        
        # If it's a dollar sign with a country code, extract the code
        if currency.endswith("$"):
            country_code = currency[:-1]
            if country_code and len(country_code) == 2:
                return country_code + "D"
        
        # If it's a Russian ruble sign (₽), return RUB
        if currency == "₽":
            return "RUB"
        
        # If it's already a 3-letter code, return as is
        if len(currency) == 3 and currency.isalpha():
            return currency
        
        # Default to USD if we can't determine the currency
        if currency in ["$", "DOLLAR", "DOLLARS"]:
            return "USD"
        
        # Return as is (the API will validate)
        return currency
    
    def _get_exchange_rates(self, base_currency: str) -> Dict[str, float]:
        """
        Fetch exchange rates from API with caching.
        
        Args:
            base_currency (str): Base currency code
        
        Returns:
            Dict[str, float]: Exchange rates dictionary
            
        Raises:
            Exception: If the API request fails
        """
        # Check if we have a fresh cache entry
        current_time = datetime.now().timestamp()
        if (base_currency in self.exchange_rates_cache and 
            current_time - self.cache_timestamp.get(base_currency, 0) < self.cache_expiry):
            print(f"Using cached exchange rates for {base_currency}")
            return self.exchange_rates_cache[base_currency]
        
        # Fetch new rates from primary API
        try:
            print(f"Fetching exchange rates for {base_currency} from primary API")
            url = f"{self.exchange_rates_url}{base_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("result") == "success":
                rates = data.get("rates", {})
                # Cache the results
                self.exchange_rates_cache[base_currency] = rates
                self.cache_timestamp[base_currency] = current_time
                return rates
            else:
                # If the primary API fails, try the backup API
                print(f"Primary API failed, trying backup API for {base_currency}")
                raise Exception("Primary API did not return success")
                
        except Exception as primary_error:
            print(f"Error with primary API: {primary_error}")
            
            try:
                # Try the backup API
                print(f"Using backup API for {base_currency}")
                params = {"base": base_currency}
                response = requests.get(self.backup_api_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get("success", False):
                    rates = data.get("rates", {})
                    # Cache the results
                    self.exchange_rates_cache[base_currency] = rates
                    self.cache_timestamp[base_currency] = current_time
                    return rates
                else:
                    raise Exception(f"Backup API failed: {data.get('error', 'Unknown error')}")
                    
            except Exception as backup_error:
                print(f"Error with backup API: {backup_error}")
                
                # If both APIs fail, return our default rates if we have them
                if "USD" in self.exchange_rates_cache:
                    print("Using USD rates as fallback")
                    usd_rates = self.exchange_rates_cache["USD"]
                    
                    # Convert USD rates to the requested base currency
                    if base_currency in usd_rates:
                        base_rate = usd_rates[base_currency]
                        converted_rates = {curr: rate / base_rate for curr, rate in usd_rates.items()}
                        return converted_rates
                
                # If everything fails, raise an exception
                raise Exception(f"Failed to fetch exchange rates for {base_currency}: {primary_error}. Backup API also failed: {backup_error}")
    
    def get_conversion_description(self, conversion_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the currency conversion.
        
        Args:
            conversion_data (Dict[str, Any]): Conversion data from convert_currency
            
        Returns:
            str: Human-readable conversion description
        """
        query = conversion_data["query"]
        result = conversion_data["result"]
        info = conversion_data["info"]
        
        amount = query["amount"]
        from_currency = query["from"]
        to_currency = query["to"]
        rate = info["rate"]
        
        description = (
            f"{amount} {from_currency} = {result['formatted']}. "
            f"Exchange rate: 1 {from_currency} = {rate:.4f} {to_currency}. "
            f"(Inverse: 1 {to_currency} = {info['inverse_rate']:.4f} {from_currency}). "
            f"This conversion was calculated at {query['timestamp']}."
        )
        
        return description

def convert_currency(amount: float, from_currency: str, to_currency: str) -> Dict[str, Any]:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount (float): The amount to convert
        from_currency (str): Source currency code (e.g., USD, EUR)
        to_currency (str): Target currency code (e.g., JPY, GBP)
    
    Returns:
        Dict[str, Any]: Conversion result with details
    """
    global _currency_tool
    try:
        _currency_tool
    except NameError:
        _currency_tool = CurrencyTool()
    
    return _currency_tool.convert_currency(amount, from_currency, to_currency)

# Create a single instance for the module
try:
    _currency_tool
except NameError:
    _currency_tool = CurrencyTool()