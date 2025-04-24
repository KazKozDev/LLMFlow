"""
Tests for the WeatherTool class.
"""

import os
import sys
print("Current directory:", os.getcwd())
print("Python path before:", sys.path)

# Add the project root to Python path
project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print("Project root:", project_root)
print("Python path after:", sys.path)

try:
    import tools
    print("Successfully imported tools package")
    from tools.weather_tool import WeatherTool
    print("Successfully imported WeatherTool")
except Exception as e:
    print("Import error:", str(e))
    import traceback
    traceback.print_exc()

import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import patch, Mock

def test_weather_tool_initialization():
    """Test WeatherTool initialization."""
    tool = WeatherTool()
    assert tool.TOOL_NAME == "weather_tool"
    assert tool.api_url.startswith("https://")
    assert tool.geocoding_url.startswith("https://")
    assert isinstance(tool.cache, dict)

@patch('requests.get')
def test_get_coordinates(mock_get):
    """Test coordinates retrieval from location."""
    tool = WeatherTool()
    
    # Mock geocoding response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'results': [{
            'latitude': 40.7128,
            'longitude': -74.0060,
            'name': 'New York',
            'country': 'United States',
            'timezone': 'America/New_York'
        }]
    }
    mock_get.return_value = mock_response
    
    coords = tool._get_coordinates("New York")
    assert coords['latitude'] == pytest.approx(40.7128)
    assert coords['longitude'] == pytest.approx(-74.0060)
    assert coords['name'] == 'New York'

@patch('requests.get')
def test_get_weather(mock_get):
    """Test weather data retrieval."""
    tool = WeatherTool()
    
    # Mock geocoding response
    mock_geocoding = Mock()
    mock_geocoding.status_code = 200
    mock_geocoding.json.return_value = {
        'results': [{
            'latitude': 40.7128,
            'longitude': -74.0060,
            'name': 'New York',
            'country': 'United States',
            'timezone': 'America/New_York'
        }]
    }
    
    # Mock weather response
    mock_weather = Mock()
    mock_weather.status_code = 200
    mock_weather.json.return_value = {
        'current': {
            'temperature_2m': 20.5,
            'windspeed_10m': 5.2,
            'winddirection_10m': 180,
            'weathercode': 1,
            'time': '2024-01-01T12:00'
        },
        'daily': {
            'time': ['2024-01-01', '2024-01-02'],
            'temperature_2m_max': [22.5, 23.0],
            'temperature_2m_min': [15.0, 16.0],
            'precipitation_probability_max': [20, 30]
        }
    }
    
    mock_get.side_effect = [mock_geocoding, mock_weather]
    
    weather = tool.get_weather("New York")
    
    assert 'current' in weather
    assert 'forecast' in weather
    assert len(weather['forecast']) > 0
    assert isinstance(weather['timestamp'], str)

def test_cache_functionality():
    """Test weather data caching."""
    tool = WeatherTool()
    location = "New York"
    
    # Create test weather data
    test_data = {
        'current': {'temperature': 20.5},
        'forecast': [{'date': '2024-01-01', 'max_temp': 22.5}],
        'timestamp': datetime.now().isoformat()
    }
    
    # Store in cache
    tool.cache[location] = test_data
    
    # Test cache retrieval
    cached_weather = tool.get_weather(location)
    assert cached_weather['current']['temperature'] == 20.5

@patch('requests.get')
def test_error_handling(mock_get):
    """Test error handling."""
    tool = WeatherTool()
    
    # Mock API error
    mock_get.side_effect = Exception("API Error")
    
    with pytest.raises(Exception) as exc_info:
        tool.get_weather("Invalid Location")
    assert "Error getting weather data" in str(exc_info.value)

def test_weather_code_interpretation():
    """Test weather code interpretation."""
    tool = WeatherTool()
    
    # Test various weather codes
    assert "Clear sky" in tool._get_weather_description(0)
    assert "Partly cloudy" in tool._get_weather_description(2)
    assert "rain" in tool._get_weather_description(61).lower()

def test_temperature_formatting():
    """Test temperature formatting."""
    tool = WeatherTool()
    
    # Test temperature conversion and formatting
    temp_c = 20.5
    temp_f = tool._celsius_to_fahrenheit(temp_c)
    assert temp_f == pytest.approx(68.9)
    
    formatted = tool._format_temperature(temp_c)
    assert "20.5°C" in formatted
    assert "68.9°F" in formatted

def test_forecast_processing():
    """Test forecast data processing."""
    tool = WeatherTool()
    
    # Test forecast data
    forecast_data = {
        'time': ['2024-01-01', '2024-01-02'],
        'temperature_2m_max': [22.5, 23.0],
        'temperature_2m_min': [15.0, 16.0],
        'precipitation_probability_max': [20, 30]
    }
    
    processed = tool._process_forecast(forecast_data)
    assert len(processed) == 2
    assert processed[0]['date'] == '2024-01-01'
    assert processed[0]['max_temp'] == 22.5
    assert processed[0]['min_temp'] == 15.0
    assert processed[0]['precipitation_chance'] == 20

@patch('requests.get')
def test_invalid_location(mock_get):
    """Test handling of invalid locations."""
    tool = WeatherTool()
    
    # Mock empty geocoding response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {'results': []}
    mock_get.return_value = mock_response
    
    with pytest.raises(Exception) as exc_info:
        tool.get_weather("NonexistentLocation")
    assert "Could not find coordinates" in str(exc_info.value)

@patch('requests.get')
def test_cache_expiration(mock_get):
    """Test cache expiration handling."""
    tool = WeatherTool()
    location = "New York"
    
    # Create expired cache data
    expired_data = {
        'current': {'temperature': 20.5},
        'forecast': [{'date': '2024-01-01', 'max_temp': 22.5}],
        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()  # 2 hours old
    }
    
    tool.cache[location] = expired_data
    
    # Mock geocoding response
    mock_geocoding = Mock()
    mock_geocoding.status_code = 200
    mock_geocoding.json.return_value = {
        'results': [{
            'latitude': 40.7128,
            'longitude': -74.0060,
            'name': 'New York',
            'country': 'United States',
            'timezone': 'America/New_York'
        }]
    }
    
    # Mock weather response
    mock_weather = Mock()
    mock_weather.status_code = 200
    mock_weather.json.return_value = {
        'current': {
            'temperature_2m': 21.0,
            'windspeed_10m': 5.2,
            'winddirection_10m': 180,
            'weathercode': 1,
            'time': '2024-01-01T12:00'
        },
        'daily': {
            'time': ['2024-01-01'],
            'temperature_2m_max': [23.0],
            'temperature_2m_min': [16.0],
            'precipitation_probability_max': [20]
        }
    }
    
    mock_get.side_effect = [mock_geocoding, mock_weather]
    
    weather = tool.get_weather(location)
    assert weather['current']['temperature'] == tool._format_temperature(21.0)  # Should get new data 