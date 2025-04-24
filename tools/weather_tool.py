# tools/weather_tool.py

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import os

class WeatherTool:
    """
    Tool Name: Weather Information Tool
    Description: Retrieves current weather data for any location without requiring API keys
    Usage: Can be used to get weather by city name or coordinates
    
    System Prompt Addition:
    ```
    You have access to a Weather Tool that can retrieve current weather information for any location.
    When a user asks about weather conditions, temperature, or other meteorological information for
    a specific location, use the weather_tool to get this information.
    
    - To check weather by city: Use weather_tool.get_weather("New York") or weather_tool.get_weather("Paris, FR")
    - To check weather by coordinates: Use weather_tool.get_weather_by_coordinates(40.7128, -74.0060)
    
    This tool doesn't require any API keys and returns detailed weather information including 
    temperature, weather conditions, wind, humidity, and precipitation data.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "weather_tool"
    TOOL_DESCRIPTION = "Get current weather and forecasts for any location"
    TOOL_PARAMETERS = [
        {"name": "location", "type": "string", "description": "Location to get weather for", "required": True},
        {"name": "country_code", "type": "string", "description": "Two-letter country code", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What's the weather in London?", "tool_call": "weather_tool.get_weather('London')"},
        {"query": "Current temperature in Tokyo", "tool_call": "weather_tool.get_weather('Tokyo')"},
        {"query": "Is it raining in Paris?", "tool_call": "weather_tool.get_weather('Paris')"},
        {"query": "какая погода в Москве", "tool_call": "weather_tool.get_weather('Moscow')"}
    ]
    
    def __init__(self):
        """Initialize the WeatherTool."""
        self.api_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.cache = {}
        self.cache_expiry = 3600  # 1 hour
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weather_cache")
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get weather for a location.
        """
        print(f"Getting weather for location: {location}")
        try:
            # Check cache first
            if location in self.cache:
                cache_data = self.cache[location]
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if (datetime.now() - cache_time).total_seconds() < self.cache_expiry:
                    print(f"Using cached weather data for {location}")
                    return cache_data

            # Get coordinates
            coords = self._get_coordinates(location)
            if not coords:
                raise Exception(f"Could not find coordinates for {location}")

            # Fetch weather data
            params = {
                'latitude': coords['latitude'],
                'longitude': coords['longitude'],
                'current': ['temperature_2m', 'windspeed_10m', 'winddirection_10m', 'weathercode'],
                'daily': ['temperature_2m_max', 'temperature_2m_min', 'precipitation_probability_max'],
                'timezone': 'auto'
            }
            response = requests.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Process the data
            weather_data = {
                'location': coords,
                'coordinates': coords,
                'current': self._process_current(data.get('current', {})),
                'forecast': self._process_forecast(data.get('daily', {})),
                'timestamp': datetime.now().isoformat()
            }

            # Cache the results
            self.cache[location] = weather_data

            return weather_data
        except Exception as e:
            raise Exception(f"Error getting weather data: {e}")
    
    def _get_coordinates(self, location: str) -> Dict[str, float]:
        """
        Get coordinates for a location.
        
        Args:
            location (str): Location name
            
        Returns:
            Dict[str, float]: Coordinates and location info
        """
        print(f"Making geocoding request for: {location}")
        try:
            params = {
                'name': location,
                'count': 1,
                'language': 'en',
                'format': 'json'
            }
            
            response = requests.get(self.geocoding_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                print(f"No results found for location: {location}")
                return {}
            
            result = results[0]
            return {
                'latitude': result['latitude'],
                'longitude': result['longitude'],
                'name': result.get('name', location),
                'country': result.get('country', ''),
                'timezone': result.get('timezone', 'UTC')
            }
            
        except Exception as e:
            print(f"Error in geocoding: {str(e)}")
            return {}
    
    def _process_current(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process current weather data."""
        if not data:
            return {}
            
        return {
            'temperature': self._format_temperature(data.get('temperature_2m', 0)),
            'wind_speed': data.get('windspeed_10m', 0),
            'wind_direction': data.get('winddirection_10m', 0),
            'description': self._get_weather_description(data.get('weathercode', 0)),
            'time': data.get('time', datetime.now().isoformat())
        }
    
    def _process_forecast(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process forecast data."""
        if not data:
            return []
            
        forecast = []
        times = data.get('time', [])
        max_temps = data.get('temperature_2m_max', [])
        min_temps = data.get('temperature_2m_min', [])
        precip_probs = data.get('precipitation_probability_max', [])
        
        for i in range(len(times)):
            forecast.append({
                'date': times[i],
                'max_temp': max_temps[i] if i < len(max_temps) else None,
                'min_temp': min_temps[i] if i < len(min_temps) else None,
                'precipitation_chance': precip_probs[i] if i < len(precip_probs) else None
            })
        
        return forecast
    
    def _celsius_to_fahrenheit(self, celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9/5) + 32
    
    def _format_temperature(self, celsius: float) -> str:
        """Format temperature in both Celsius and Fahrenheit."""
        fahrenheit = self._celsius_to_fahrenheit(celsius)
        return f"{celsius:.1f}°C ({fahrenheit:.1f}°F)"
    
    def _get_weather_description(self, code: int) -> str:
        """Get weather description from code."""
        descriptions = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snow fall",
            73: "Moderate snow fall",
            75: "Heavy snow fall",
            77: "Snow grains",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers",
            85: "Slight snow showers",
            86: "Heavy snow showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return descriptions.get(code, "Unknown")

    def get_weather_description(self, weather_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the weather data.
        
        Args:
            weather_data (Dict[str, Any]): Formatted weather data from WeatherTool
            
        Returns:
            str: Human-readable weather description
        """
        location = f"{weather_data['location']['name']}, {weather_data['location']['country']}"
        condition = weather_data['current']['description']
        temp = weather_data['current']['temperature']
        humidity = "N/A"
        wind_speed = weather_data['current']['wind_speed']
        
        description = (
            f"Current weather in {location}: {condition}. "
            f"Temperature is {temp}. "
            f"Humidity is {humidity}%. "
            f"Wind speed is {wind_speed} m/s. "
        )
        
        return description

# Function to expose to the LLM tool system
def get_weather(location):
    """
    Get weather information for a location
    
    Args:
        location (str): City name or coordinates
        
    Returns:
        str: Weather information in natural language
    """
    try:
        print(f"get_weather function called with location: {location}")
        tool = WeatherTool()
        weather_data = tool.get_weather(location)
        description = tool.get_weather_description(weather_data)
        print(f"Weather description: {description}")
        return description
    except Exception as e:
        error_msg = f"Error getting weather: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg