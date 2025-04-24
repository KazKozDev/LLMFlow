import pytest
import unittest.mock
from unittest.mock import patch, MagicMock
from datetime import datetime
import ephem

# Import the tool class and functions to be tested
# Adjust imports based on the actual structure of astronomy_tool.py
try:
    from tools.astronomy_tool import (
        AstronomyTool,
        get_celestial_events,
        get_eclipse_info,
        get_visible_constellations,
        get_planet_info,
        Season, # Import Enums/Dataclasses if needed for mocking/assertions
        ConstellationInfo,
        PlanetInfo
    )
    # Assume a_tool instance might be used directly by wrappers, need to handle its state if necessary
    from tools.astronomy_tool import a_tool as astronomy_tool_instance
except ImportError as e:
    pytest.fail(f"Failed to import astronomy tool components: {e}")

# Basic test class structure
class TestAstronomyTool:

    # Example mock data (adjust as needed based on actual tool data structures)
    MOCK_PLANET_DATA = {
        "info": {
            "name": "Mars",
            "type": "Terrestrial planet",
            "diameter": "6,792",
            "mass": "6.39 × 10^23",
            "orbital_period": "687 Earth days",
            "rotation_period": "24 hours 37 minutes",
            "average_temperature": "-63°C",
            "moons": 2,
            "rings": False,
            "description": "The Red Planet...",
            "interesting_facts": ["Fact 1", "Fact 2"]
        },
        "current_data": {
            "distance_from_earth": {"au": 1.5, "km": "224,396,806"},
            "constellation": "Leo",
            "magnitude": -0.5,
            "phase": 95.0,
            "observable": True
        },
        "fetched_at": "2024-07-26T12:00:00Z"
    }

    MOCK_CONSTELLATION_DATA = {
         "constellations": [
             {
                "name": "Orion", "latin_name": "Orion", "description": "The Hunter...",
                 "notable_stars": ["Betelgeuse", "Rigel"], "mythology": "Myth...",
                 "seasonal_visibility": True, "best_viewing_time": "Evening"
             },
              {
                "name": "Ursa Major", "latin_name": "Ursa Major", "description": "The Great Bear...",
                 "notable_stars": ["Alioth", "Dubhe"], "mythology": "Myth...",
                 "seasonal_visibility": False, "best_viewing_time": "Variable"
             }
         ],
         "location": "London",
         "coordinates": {"latitude": 51.5074, "longitude": -0.1278},
         "date": "2024-01-15",
         "season": "Winter",
         "fetched_at": "2024-07-26T12:00:00Z"
    }

    MOCK_ECLIPSE_DATA = {
        "eclipses": [
            {"type": "Partial Lunar Eclipse", "date": "September 18, 2024", "visibility": "Americas, Europe, Africa", "details_link": "...", "source": "TimeAndDate.com"},
            {"type": "Annular Solar Eclipse", "date": "October 2, 2024", "visibility": "Pacific, S. America", "details_link": "...", "source": "TimeAndDate.com"}
        ],
        "location": None,
        "source": "TimeAndDate.com",
        "fetched_at": "2024-07-26T12:00:00Z"
    }

    MOCK_CELESTIAL_EVENTS_DATA = {
        "events": [
            {"name": "Perseid Meteor Shower Peak", "date": "August 12, 2024", "description": "...", "type": "meteor shower", "source": "TimeAndDate.com"},
            {"name": "Saturn at Opposition", "date": "September 8, 2024", "description": "...", "type": "opposition", "source": "TimeAndDate.com"}
        ],
        "location": None,
        "source": "TimeAndDate.com",
        "fetched_at": "2024-07-26T12:00:00Z"
    }

    # --- Tests for get_planet_info ---

    @patch('tools.astronomy_tool.a_tool.get_planet_data')
    def test_get_planet_info_valid(self, mock_get_data):
        """Test get_planet_info for a valid planet (Mars)."""
        # Use the mock data defined in the class
        mock_get_data.return_value = self.MOCK_PLANET_DATA
        planet_name = "Mars"

        result_str = get_planet_info(planet_name)

        # Assert with positional argument
        mock_get_data.assert_called_once_with(planet_name)
        # Check for key details from the formatted output
        assert "Mars - Terrestrial planet" in result_str
        assert "Diameter: 6,792 km" in result_str
        assert "Average Temperature: -63°C" in result_str
        assert "Currently in constellation: Leo" in result_str # From mock data
        assert "Brightness (magnitude): -0.5" in result_str
        assert "Visible to naked eye: Yes" in result_str
        assert "Fact 1" in result_str # Check interesting facts
        assert "Fetched at:" in result_str # Check fetch timestamp presence

    @patch('tools.astronomy_tool.a_tool.get_planet_data')
    def test_get_planet_info_invalid_name(self, mock_get_data):
        """Test get_planet_info with an invalid planet name."""
        invalid_planet = "Pluto"
        # Simulate the error structure returned by get_planet_data for ValueError
        mock_get_data.return_value = {
            "error": f"Unknown planet: {invalid_planet}",
            "fetched_at": datetime.utcnow().isoformat() # Include timestamp as the real method does
        }

        result_str = get_planet_info(invalid_planet)

        # Assert with positional argument
        mock_get_data.assert_called_once_with(invalid_planet)
        # The wrapper function calls the formatter which handles the error dict
        assert "Error retrieving planet information: Unknown planet: Pluto" in result_str

    @patch('tools.astronomy_tool.a_tool.get_planet_data')
    def test_get_planet_info_internal_error(self, mock_get_data):
        """Test get_planet_info when the underlying method raises an unexpected Exception."""
        planet_name = "Venus"
        error_message = "ephem calculation failed unexpectedly"
        # Simulate the get_planet_data method raising an Exception
        mock_get_data.side_effect = Exception(error_message)

        result_str = get_planet_info(planet_name)

        # Assert with positional argument
        mock_get_data.assert_called_once_with(planet_name)
        # Check the error message generated by the wrapper function's except block
        assert f"An unexpected error occurred while getting planet information: {error_message}" in result_str

    # --- Tests for get_visible_constellations ---

    @patch('tools.astronomy_tool.a_tool.get_visible_constellations_data')
    @patch('tools.astronomy_tool.datetime') # Patch datetime to control "tonight"/default date
    def test_get_visible_constellations_valid(self, mock_datetime, mock_get_data):
        """Test get_visible_constellations with valid location and date."""
        # Mock utcnow used by the underlying method if date is None or 'tonight'
        mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 22, 0, 0) # A winter date
        # Use the mock data from the class, assuming it represents Winter in London
        mock_get_data.return_value = self.MOCK_CONSTELLATION_DATA
        location = "London"
        date_str = "2024-01-15"

        result_str = get_visible_constellations(location, date_str)

        mock_get_data.assert_called_once_with(location=location, date=date_str)
        assert "Visible Constellations for London" in result_str
        assert "(Lat: 51.51°, Lon: -0.13°)" in result_str # Check coords format
        assert "Date: 2024-01-15 (Winter)" in result_str
        assert "• Orion (Orion)" in result_str
        assert "Best viewing: Evening" in result_str # For Orion in Winter
        assert "• Ursa Major (Ursa Major)" in result_str
        assert "Best viewing: Variable" in result_str # For Ursa Major in Winter
        assert "Fetched at:" in result_str

    @patch('tools.astronomy_tool.a_tool.get_visible_constellations_data')
    @patch('tools.astronomy_tool.datetime')
    def test_get_visible_constellations_tonight(self, mock_datetime, mock_get_data):
        """Test get_visible_constellations with date='tonight'."""
        mock_datetime.utcnow.return_value = datetime(2024, 7, 15, 22, 0, 0) # A summer date
        # Modify mock data slightly for summer expectation
        mock_data_summer = self.MOCK_CONSTELLATION_DATA.copy()
        mock_data_summer["date"] = "2024-07-15"
        mock_data_summer["season"] = "Summer"
        # Update visibility based on summer season (e.g., Ursa Major might be better)
        # This assumes the underlying logic correctly calculates season
        mock_get_data.return_value = mock_data_summer
        location = "London"

        result_str = get_visible_constellations(location, date='tonight')

        # Underlying method receives date='tonight'
        mock_get_data.assert_called_once_with(location=location, date='tonight')
        assert "Visible Constellations for London" in result_str
        assert "Date: 2024-07-15 (Summer)" in result_str # Check date/season derived from mock utcnow

    # We need to mock the potential import of geolocation_tool
    @patch.dict('sys.modules', {'geolocation_tool': MagicMock()})
    @patch('tools.astronomy_tool.a_tool.get_visible_constellations_data')
    @patch('tools.astronomy_tool.datetime')
    def test_get_visible_constellations_unknown_location_fallback(self, mock_datetime, mock_get_data):
        """Test fallback to default location (London) if geolocation fails."""
        # Mock utcnow for consistent date
        mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 22, 0, 0) # Winter date
        # Mock the geolocation tool to simulate failure
        # Access the mocked module via sys.modules if needed, but not needed for this test setup
        # sys.modules['geolocation_tool'].get_location_info.return_value = None

        # Use standard mock data, expecting London defaults
        mock_get_data.return_value = self.MOCK_CONSTELLATION_DATA
        unknown_location = "Atlantis"

        result_str = get_visible_constellations(unknown_location)

        # Underlying method called with the unknown location
        mock_get_data.assert_called_once_with(location=unknown_location, date=None)
        # Assert output reflects London default used internally by get_visible_constellations_data
        assert "Visible Constellations for London" in result_str
        # The mock data returned should be for London
        assert "(Lat: 51.51°, Lon: -0.13°)" in result_str
        assert "Date: 2024-01-15 (Winter)" in result_str

    @patch('tools.astronomy_tool.a_tool.get_visible_constellations_data')
    def test_get_visible_constellations_internal_error(self, mock_get_data):
        """Test get_visible_constellations when the underlying method raises an Exception."""
        location = "London"
        error_message = "ephem observer failed"
        mock_get_data.side_effect = Exception(error_message)

        result_str = get_visible_constellations(location)

        mock_get_data.assert_called_once_with(location=location, date=None)
        assert f"An unexpected error occurred while getting constellation information: {error_message}" in result_str

    # Placeholder test
    def test_placeholder_astronomy(self):
        assert True

    # --- Tests for get_eclipse_info ---

    @patch('tools.astronomy_tool.a_tool.get_eclipse_info')
    def test_get_eclipse_info_global(self, mock_get_data):
        """Test get_eclipse_info without a location (global list)."""
        mock_get_data.return_value = self.MOCK_ECLIPSE_DATA

        result_str = get_eclipse_info()

        mock_get_data.assert_called_once_with(None)
        assert "Upcoming Eclipses:" in result_str
        assert "• Partial Lunar Eclipse" in result_str
        assert "Date: September 18, 2024" in result_str
        assert "Visibility: Americas, Europe, Africa" in result_str
        assert "• Annular Solar Eclipse" in result_str
        assert "Date: October 2, 2024" in result_str
        assert "Source: TimeAndDate.com" in result_str
        assert "potentially visible from" not in result_str # Check location filter is not mentioned

    @patch('tools.astronomy_tool.a_tool.get_eclipse_info')
    def test_get_eclipse_info_with_location(self, mock_get_data):
        """Test get_eclipse_info with a specific location."""
        # Simulate data possibly filtered/reordered for the location
        mock_data_location = {
            "eclipses": [
                 {"type": "Annular Solar Eclipse", "date": "October 2, 2024", "visibility": "Pacific, S. America", "details_link": "...", "source": "TimeAndDate.com"}, # Assume this is more relevant
                 {"type": "Partial Lunar Eclipse", "date": "September 18, 2024", "visibility": "Americas, Europe, Africa", "details_link": "...", "source": "TimeAndDate.com"}
            ],
            "location": "Santiago",
            "source": "TimeAndDate.com",
            "fetched_at": "2024-07-26T12:05:00Z"
        }
        mock_get_data.return_value = mock_data_location
        location = "Santiago"

        result_str = get_eclipse_info(location)

        mock_get_data.assert_called_once_with(location)
        assert f"Upcoming Eclipses potentially visible from {location}" in result_str
        assert "• Annular Solar Eclipse" in result_str # Check content based on mock
        assert "Date: October 2, 2024" in result_str

    @patch('tools.astronomy_tool.a_tool.get_eclipse_info')
    def test_get_eclipse_info_error(self, mock_get_data):
        """Test get_eclipse_info when the underlying method raises an Exception."""
        error_message = "Web request timed out"
        mock_get_data.side_effect = Exception(error_message)
        location = "London"

        result_str = get_eclipse_info(location)

        mock_get_data.assert_called_once_with(location)
        assert f"An unexpected error occurred in the tool wrapper: {error_message}" in result_str

    # --- Tests for get_celestial_events ---

    @patch('tools.astronomy_tool.a_tool.get_celestial_events')
    def test_get_celestial_events_no_filters(self, mock_get_data):
        """Test get_celestial_events with no date or location filters."""
        mock_get_data.return_value = self.MOCK_CELESTIAL_EVENTS_DATA

        result_str = get_celestial_events()

        # Check underlying method called with Nones
        mock_get_data.assert_called_once_with(date=None, location=None)
        assert "Upcoming Celestial Events:" in result_str
        assert "• Perseid Meteor Shower Peak" in result_str
        assert "Date: August 12, 2024" in result_str
        assert "• Saturn At Opposition" in result_str # Title case check
        assert "Date: September 8, 2024" in result_str
        assert "Source: TimeAndDate.com" in result_str

    @patch('tools.astronomy_tool.a_tool.get_celestial_events')
    def test_get_celestial_events_with_date_filter(self, mock_get_data):
        """Test get_celestial_events passing a date filter."""
        # Simulate data possibly filtered by date (e.g., only August events)
        mock_data_filtered = {
            "events": [
                {"name": "Perseid Meteor Shower Peak", "date": "August 12, 2024", "description": "...", "type": "meteor shower", "source": "TimeAndDate.com"}
            ],
            "location": None,
            "source": "TimeAndDate.com",
            "fetched_at": "2024-07-26T12:10:00Z"
        }
        mock_get_data.return_value = mock_data_filtered
        date_filter = "August"

        result_str = get_celestial_events(date=date_filter)

        # Check underlying method called with the date filter
        mock_get_data.assert_called_once_with(date=date_filter, location=None)
        assert "Upcoming Celestial Events:" in result_str
        assert "• Perseid Meteor Shower Peak" in result_str
        assert "• Saturn At Opposition" not in result_str # Check that other event is not present

    @patch('tools.astronomy_tool.a_tool.get_celestial_events')
    def test_get_celestial_events_with_location(self, mock_get_data):
        """Test get_celestial_events passing a location (used for context only)."""
        # Return the standard mock data as location doesn't filter events
        mock_get_data.return_value = self.MOCK_CELESTIAL_EVENTS_DATA
        location = "Tokyo"

        result_str = get_celestial_events(location=location)

        # Check underlying method called with the location
        mock_get_data.assert_called_once_with(date=None, location=location)
        assert "Upcoming Celestial Events:" in result_str
        assert "• Perseid Meteor Shower Peak" in result_str
        assert "• Saturn At Opposition" in result_str

    @patch('tools.astronomy_tool.a_tool.get_celestial_events')
    def test_get_celestial_events_error(self, mock_get_data):
        """Test get_celestial_events when the underlying method raises an Exception."""
        error_message = "Failed parsing In-The-Sky.org"
        mock_get_data.side_effect = Exception(error_message)
        date_filter = "September"

        result_str = get_celestial_events(date=date_filter)

        mock_get_data.assert_called_once_with(date=date_filter, location=None)
        assert f"An unexpected error occurred in the tool wrapper: {error_message}" in result_str

    # Placeholder test
    def test_placeholder_astronomy(self):
        assert True

# Tests will be added here for:
# - get_planet_info
# - get_visible_constellations
# - get_eclipse_info
# - get_celestial_events
# - Formatting functions (if desirable to test separately)
# - Error handling (invalid planet names, locations, dates)

# More tests will be added here for:
# - AstronomyTool class initialization
# - get_eclipse_info function (mocking web requests/parsing)
# - get_celestial_events function (mocking web requests/parsing)
# - get_visible_constellations function (mocking ephem/geolocation)
# - get_planet_info function (mocking ephem)
# - Formatting functions (format_eclipse_info, etc.)
# - Helper functions (_parse_date_from_title, etc.)
# - Edge cases (e.g., bad location, invalid date, API errors) 