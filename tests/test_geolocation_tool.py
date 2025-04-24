import pytest
import requests
import unittest.mock
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import the tool class and functions to be tested
# Adjust imports based on the actual structure of geolocation_tool.py
from tools.geolocation_tool import GeolocationTool, get_location_info, get_location_from_coordinates, calculate_distance, find_nearby_places

# --- Mock Data ---

# Mock raw API response for Nominatim search
MOCK_NOMINATIM_RESPONSE_PARIS = [
    {
        "place_id": 12345,
        "licence": "Data © OpenStreetMap contributors, ODbL 1.0. https://osm.org/copyright",
        "osm_type": "relation",
        "osm_id": 71525,
        "lat": "48.8571658",
        "lon": "2.3516168",
        "display_name": "Paris, Ile-de-France, France",
        "address": {
            "city": "Paris",
            "state": "Ile-de-France",
            "country": "France",
            "country_code": "fr"
        },
        "boundingbox": ["48.8155", "48.9021", "2.2241", "2.4699"],
        "extratags": {"wikidata": "Q90"},
        "namedetails": {"name": "Paris"},
        "class": "boundary",
        "type": "administrative"
    }
]

# Mock formatted data expected from _format_location_data
MOCK_FORMATTED_DATA_PARIS = {
    'query': 'Paris, France', # This should be added by the wrapper/caller
    'results': [
        {
            'name': 'Paris',
            'display_name': 'Paris, Ile-de-France, France',
            'latitude': 48.8571658,
            'longitude': 2.3516168,
            'type': 'administrative', # Note: type comes from class/type
            'country': 'France',
            'address': { 
                'city': 'Paris', 
                'state': 'Ile-de-France', 
                'country': 'France', 
                'country_code': 'fr'
            },
            'bounding_box': {
                'min_lat': 48.8155, 'max_lat': 48.9021, 
                'min_lon': 2.2241, 'max_lon': 2.4699
            },
            'osm_id': 71525,
            'wikidata_id': 'Q90'
        }
    ],
    'source': 'Nominatim/OpenStreetMap',
    'timestamp': datetime(2024, 4, 24, 14, 0, 0).isoformat() # Assuming timestamp is added
}

# --- Test Class ---

class TestGeolocationTool:

    # Patch the *internal* get_location_info method of the GeolocationTool class
    @patch('tools.geolocation_tool.GeolocationTool.get_location_info')
    def test_get_location_info_success(self, mock_internal_get_info):
        """Test the get_location_info wrapper for a successful lookup."""
        # Configure the mock to return the formatted dictionary data
        mock_internal_get_info.return_value = MOCK_FORMATTED_DATA_PARIS
        
        location_query = "Paris, France"
        
        # Call the wrapper function
        result_str = get_location_info(location_query)
        
        # Check that the internal method was called correctly
        mock_internal_get_info.assert_called_once_with(location_query)
        
        # Check the STRING output of the wrapper function
        assert "Paris is located at Paris, Ile-de-France, France." in result_str
        assert "Coordinates: 48.8571658, 2.3516168" in result_str
        assert "City: Paris" in result_str
        assert "Country: France" in result_str

    @patch('tools.geolocation_tool.GeolocationTool.get_location_info')
    def test_get_location_info_not_found(self, mock_internal_get_info):
        """Test get_location_info wrapper when the location is not found."""
        error_message = "Location 'NonExistentPlace123' not found"
        mock_internal_get_info.side_effect = Exception(error_message)
        
        location_query = "NonExistentPlace123"
        
        # Call the wrapper and check the returned error string
        result_str = get_location_info(location_query)
        mock_internal_get_info.assert_called_once_with(location_query)
        assert f"Error getting location info: {error_message}" in result_str

    @patch('tools.geolocation_tool.GeolocationTool.get_location_info')
    def test_get_location_info_api_error(self, mock_internal_get_info):
        """Test get_location_info wrapper when the API request fails."""
        error_message = "Error in geocoding request: Network Error"
        mock_internal_get_info.side_effect = Exception(error_message)
        
        location_query = "SomePlace"
        
        # Call the wrapper and check the returned error string
        result_str = get_location_info(location_query)
        mock_internal_get_info.assert_called_once_with(location_query)
        assert f"Error getting location info: {error_message}" in result_str

    # Placeholder test (can be removed later)
    # def test_placeholder(self):
    #     assert True

# More tests will be added here for:
# - GeolocationTool class initialization (if applicable)
# - get_location_info function (mocking API calls/parsing)
# - Handling different location query types (city, address, landmark)
# - Handling ambiguous locations
# - Edge cases (e.g., location not found, API errors)
# - Helper functions if any 