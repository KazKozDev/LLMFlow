import pytest
from unittest.mock import patch, Mock
from tools.air_quality_tool import AirQualityTool

class TestAirQualityTool:
    @pytest.fixture
    def tool(self):
        return AirQualityTool()

    def test_initialization(self, tool):
        """Test tool initialization and metadata."""
        assert tool.TOOL_NAME == "air_quality_tool"
        assert isinstance(tool.TOOL_DESCRIPTION, str)
        assert len(tool.user_agents) > 0
        assert isinstance(tool.cache, dict)
        assert isinstance(tool.aqi_categories, dict)
        assert isinstance(tool.pollutants_info, dict)

    def test_get_random_user_agent(self, tool):
        """Test random user agent selection."""
        agent = tool.get_random_user_agent()
        assert isinstance(agent, str)
        assert agent in tool.user_agents

    @patch("tools.air_quality_tool.AirQualityTool._get_waqi_data")
    def test_get_air_quality_waqi_success(self, mock_waqi, tool):
        """Test successful air quality retrieval using WAQI."""
        mock_data = {
            "air_quality": {
                "aqi": 50,
                "category": "good",
                "pollutants": {
                    "pm25": 15,
                    "pm10": 30,
                    "o3": 45
                }
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_waqi.return_value = mock_data
        
        result = tool.get_air_quality("New York")
        
        assert result["air_quality"]["aqi"] == 50
        assert result["air_quality"]["category"] == "good"
        assert result["location"] == "New York"
        assert result["data_source"] == "WAQI"
        assert "pollutants" in result["air_quality"]
        assert "recommendations" in result

    @patch("tools.air_quality_tool.AirQualityTool._get_waqi_data")
    @patch("tools.air_quality_tool.AirQualityTool._get_iqair_data")
    def test_get_air_quality_fallback(self, mock_iqair, mock_waqi, tool):
        """Test fallback to IQAir when WAQI fails."""
        mock_waqi.side_effect = Exception("WAQI failed")
        mock_iqair_data = {
            "air_quality": {
                "aqi": 75,
                "category": "moderate",
                "pollutants": {
                    "pm25": 25,
                    "pm10": 40
                }
            },
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_iqair.return_value = mock_iqair_data
        
        result = tool.get_air_quality("Beijing")
        
        assert result["air_quality"]["aqi"] == 75
        assert result["air_quality"]["category"] == "moderate"
        assert result["location"] == "Beijing"
        assert result["data_source"] == "IQAir"

    def test_is_coordinates(self, tool):
        """Test coordinate string detection."""
        assert tool._is_coordinates("40.7128, -74.0060")
        assert tool._is_coordinates("40.7128,-74.0060")
        assert not tool._is_coordinates("New York")
        assert not tool._is_coordinates("12345")

    def test_extract_coordinates(self, tool):
        """Test coordinate extraction from string."""
        coords = tool._extract_coordinates("40.7128, -74.0060")
        assert coords == (40.7128, -74.0060)
        
        coords = tool._extract_coordinates("40.7128,-74.0060")
        assert coords == (40.7128, -74.0060)
        
        assert tool._extract_coordinates("invalid") is None

    @patch("tools.air_quality_tool.requests.get")
    def test_get_waqi_data(self, mock_get, tool):
        """Test WAQI API data retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "ok",
            "data": {
                "aqi": 50,
                "iaqi": {
                    "pm25": {"v": 15},
                    "pm10": {"v": 30},
                    "o3": {"v": 45}
                },
                "time": {"iso": "2024-01-01T12:00:00Z"}
            }
        }
        mock_get.return_value = mock_response
        
        result = tool._get_waqi_data("New York")
        
        assert isinstance(result, dict)
        assert "air_quality" in result
        assert result["air_quality"]["aqi"] == 50
        assert "pollutants" in result["air_quality"]
        assert result["air_quality"]["pollutants"]["pm25"] == 15

    @patch("tools.air_quality_tool.requests.get")
    def test_get_waqi_data_error(self, mock_get, tool):
        """Test WAQI API error handling."""
        mock_get.side_effect = Exception("API Error")
        
        result = tool._get_waqi_data("Invalid City")
        assert isinstance(result, dict)
        assert "error" in result
        assert "API Error" in result["error"]

    def test_get_air_quality_description(self, tool):
        """Test air quality description generation."""
        test_data = {
            "air_quality": {
                "aqi": 45,
                "category": "good",
                "pollutants": {
                    "pm25": 15,
                    "pm10": 30,
                    "o3": 45
                }
            },
            "location": "Test City",
            "timestamp": "2024-01-01T12:00:00Z",
            "data_source": "Test",
            "recommendations": ["Enjoy outdoor activities"]
        }
        
        description = tool.get_air_quality_description(test_data)
        
        assert "Test City" in description
        assert "Air Quality Index (AQI): 45" in description
        assert "Good" in description
        assert "PM2.5" in description
        assert "PM10" in description
        assert "O₃" in description
        assert "Enjoy outdoor activities" in description

    @patch("tools.air_quality_tool.AirQualityTool.get_air_quality")
    def test_wrapper_get_air_quality(self, mock_get_air_quality):
        """Test the wrapper function for get_air_quality."""
        from tools.air_quality_tool import get_air_quality
        
        mock_data = {
            "air_quality": {
                "aqi": 50,
                "category": "good",
                "pollutants": {"pm25": 15}
            },
            "location": "Test City",
            "timestamp": "2024-01-01T12:00:00Z",
            "data_source": "Test",
            "recommendations": ["Enjoy outdoor activities"]
        }
        mock_get_air_quality.return_value = mock_data
        
        result = get_air_quality("Test City")
        assert isinstance(result, str)
        assert "Test City" in result
        assert "Air Quality Index (AQI): 50" in result
        assert "Good" in result

    @patch("tools.air_quality_tool.AirQualityTool.get_air_quality_by_coordinates")
    def test_wrapper_get_air_quality_by_coordinates(self, mock_get_coords):
        """Test the wrapper function for get_air_quality_by_coordinates."""
        from tools.air_quality_tool import get_air_quality_by_coordinates
        
        mock_data = {
            "air_quality": {
                "aqi": 60,
                "category": "moderate",
                "pollutants": {"pm25": 20}
            },
            "location": "40.7128, -74.0060",
            "timestamp": "2024-01-01T12:00:00Z",
            "data_source": "Test",
            "recommendations": ["Unusually sensitive people should consider reducing prolonged outdoor exertion"]
        }
        mock_get_coords.return_value = mock_data
        
        result = get_air_quality_by_coordinates(40.7128, -74.0060)
        assert isinstance(result, str)
        assert "40.7128, -74.0060" in result
        assert "Air Quality Index (AQI): 60" in result
        assert "Moderate" in result 