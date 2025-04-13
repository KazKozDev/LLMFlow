# tools/weather_tool.py

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

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
    TOOL_DESCRIPTION = "Get current weather information for any location"
    TOOL_PARAMETERS = [
        {"name": "location", "type": "string", "description": "City name or coordinates", "required": True}
    ]
    TOOL_EXAMPLES = [
        {"query": "What's the weather in London?", "tool_call": "weather_tool.get_weather('London')"},
        {"query": "Current temperature in Tokyo", "tool_call": "weather_tool.get_weather('Tokyo')"},
        {"query": "Is it raining in Paris?", "tool_call": "weather_tool.get_weather('Paris')"},
        {"query": "какая погода в Москве", "tool_call": "weather_tool.get_weather('Moscow')"}
    ]
    
    def __init__(self):
        """Initialize the WeatherTool with free API endpoints."""
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.weather_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a specified location.
        
        Args:
            location (str): City name with optional country code (e.g., "London" or "Paris, FR")
        
        Returns:
            Dict[str, Any]: Formatted weather data
            
        Raises:
            Exception: If the API request fails
        """
        print(f"Getting weather for location: {location}")
        
        # Check if location contains a comma (city, country format)
        if "," in location:
            parts = [part.strip() for part in location.split(",")]
            city = parts[0]
            country_code = parts[1] if len(parts) > 1 else None
        else:
            city = location
            country_code = None
        
        # Check if the input might be coordinates
        if all(c.isdigit() or c in ".-," for c in location):
            try:
                if "," in location:
                    lat, lon = map(float, [p.strip() for p in location.split(",")])
                    return self.get_weather_by_coordinates(lat, lon)
            except (ValueError, TypeError):
                pass  # Not valid coordinates, proceed with city name
                
        return self.get_weather_by_city(city, country_code)
    
    def get_weather_by_city(self, city: str, country_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get current weather for a specified city.
        
        Args:
            city (str): City name
            country_code (str, optional): Two-letter country code
        
        Returns:
            Dict[str, Any]: Formatted weather data
            
        Raises:
            Exception: If the API request fails
        """
        # Step 1: Convert city name to coordinates
        print(f"Converting city '{city}' to coordinates...")
        coordinates = self._get_coordinates(city, country_code)
        if not coordinates:
            raise Exception(f"Could not find coordinates for {city}")
        
        print(f"Found coordinates for {city}: {coordinates['latitude']}, {coordinates['longitude']}")
        
        # Step 2: Get weather data for those coordinates
        return self.get_weather_by_coordinates(coordinates['latitude'], coordinates['longitude'])
    
    def get_weather_by_coordinates(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get current weather for specified coordinates.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
        
        Returns:
            Dict[str, Any]: Formatted weather data
            
        Raises:
            Exception: If the API request fails
        """
        print(f"Getting weather for coordinates: {lat}, {lon}")
        params = {
            'latitude': lat,
            'longitude': lon,
            'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m',
            'timezone': 'auto',
            'forecast_days': 1
        }
        
        try:
            print(f"Making request to Open-Meteo API...")
            response = requests.get(self.weather_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            print(f"Got response from API, formatting data...")
            return self._format_response(data, lat, lon)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error occurred: {e}"
            print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error. Please check your internet connection."
            print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again later."
            print(error_msg)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error occurred: {e}"
            print(error_msg)
            raise Exception(error_msg)
        except json.JSONDecodeError:
            error_msg = "Error decoding the API response."
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred: {e}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _get_coordinates(self, city: str, country_code: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Convert a city name to latitude and longitude coordinates.
        
        Args:
            city (str): City name
            country_code (str, optional): Two-letter country code
            
        Returns:
            Optional[Dict[str, float]]: Dictionary with latitude and longitude, or None if not found
        """
        location = city
        if country_code:
            location = f"{city},{country_code}"
            
        params = {
            'name': location,
            'count': 1,
            'language': 'en',
            'format': 'json'
        }
        
        try:
            print(f"Making geocoding request for: {location}")
            response = requests.get(self.geocoding_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                return {
                    'latitude': result['latitude'],
                    'longitude': result['longitude'],
                    'city': result['name'],
                    'country': result.get('country', ''),
                    'country_code': result.get('country_code', '').upper()
                }
            print(f"No results found for location: {location}")
            return None
            
        except Exception as e:
            print(f"Error in geocoding: {e}")
            return None
    
    def _format_response(self, data: Dict[str, Any], lat: float, lon: float) -> Dict[str, Any]:
        """
        Format the raw API response into a cleaner structure.
        
        Args:
            data (Dict[str, Any]): Raw API response
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Dict[str, Any]: Formatted weather data
        """
        # Get location info from coordinates (reverse lookup)
        location_info = self._get_location_name(lat, lon)
        
        # Weather code mapping
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            56: "Light freezing drizzle",
            57: "Dense freezing drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            66: "Light freezing rain",
            67: "Heavy freezing rain",
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
        
        # Extract current weather
        current = data['current']
        weather_code = current['weather_code']
        
        # Format the response
        formatted_data = {
            "location": {
                "city": location_info.get('city', 'Unknown'),
                "country": location_info.get('country', 'Unknown'),
                "country_code": location_info.get('country_code', 'XX'),
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                }
            },
            "time": {
                "observation_time": current['time'],
                "timezone": data['timezone'],
                "is_day": current['is_day'] == 1
            },
            "weather": {
                "condition": weather_codes.get(weather_code, "Unknown"),
                "weather_code": weather_code
            },
            "temperature": {
                "current": current['temperature_2m'],
                "feels_like": current['apparent_temperature'],
                "unit": data['current_units']['temperature_2m']
            },
            "atmospheric": {
                "pressure": current['surface_pressure'],
                "pressure_unit": data['current_units']['surface_pressure'],
                "humidity": current['relative_humidity_2m'],
                "humidity_unit": data['current_units']['relative_humidity_2m'],
                "cloud_cover": current['cloud_cover'],
                "cloud_cover_unit": data['current_units']['cloud_cover']
            },
            "wind": {
                "speed": current['wind_speed_10m'],
                "speed_unit": data['current_units']['wind_speed_10m'],
                "direction": current['wind_direction_10m'],
                "direction_unit": data['current_units']['wind_direction_10m'],
                "gusts": current['wind_gusts_10m'],
                "gusts_unit": data['current_units']['wind_gusts_10m']
            },
            "precipitation": {
                "precipitation": current['precipitation'],
                "precipitation_unit": data['current_units']['precipitation'],
                "rain": current['rain'],
                "rain_unit": data['current_units']['rain'],
                "showers": current['showers'],
                "showers_unit": data['current_units']['showers'],
                "snowfall": current['snowfall'],
                "snowfall_unit": data['current_units']['snowfall']
            }
        }
        
        return formatted_data
    
    def _get_location_name(self, lat: float, lon: float) -> Dict[str, str]:
        """
        Get city and country name from coordinates using the OpenStreetMap Nominatim API.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Dict[str, str]: Dictionary with city, country, and country_code
        """
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json'
            }
            headers = {
                'User-Agent': 'WeatherToolForLLM/1.0'  # Required by Nominatim
            }
            
            print(f"Making reverse geocoding request for coordinates: {lat}, {lon}")
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            address = data.get('address', {})
            
            return {
                'city': address.get('city', address.get('town', address.get('village', 'Unknown'))),
                'country': address.get('country', 'Unknown'),
                'country_code': address.get('country_code', 'XX').upper()
            }
        except Exception as e:
            print(f"Error in reverse geocoding: {e}")
            # Default to coordinates if reverse geocoding fails
            return {
                'city': f"Location at {lat:.2f},{lon:.2f}",
                'country': 'Unknown',
                'country_code': 'XX'
            }

    def get_weather_description(self, weather_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the weather data.
        
        Args:
            weather_data (Dict[str, Any]): Formatted weather data from WeatherTool
            
        Returns:
            str: Human-readable weather description
        """
        location = f"{weather_data['location']['city']}, {weather_data['location']['country']}"
        condition = weather_data['weather']['condition']
        temp = weather_data['temperature']['current']
        feels_like = weather_data['temperature']['feels_like']
        temp_unit = weather_data['temperature']['unit']
        humidity = weather_data['atmospheric']['humidity']
        wind_speed = weather_data['wind']['speed']
        wind_unit = weather_data['wind']['speed_unit']
        
        precipitation = weather_data['precipitation']['precipitation']
        precip_unit = weather_data['precipitation']['precipitation_unit']
        
        description = (
            f"Current weather in {location}: {condition}. "
            f"Temperature is {temp}{temp_unit}, feels like {feels_like}{temp_unit}. "
            f"Humidity is {humidity}%. "
            f"Wind speed is {wind_speed} {wind_unit}. "
        )
        
        if precipitation > 0:
            description += f"Precipitation: {precipitation} {precip_unit}. "
        
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