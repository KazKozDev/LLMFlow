import pytest

# Smoke tests for untested tools
from tools.astronomy_tool import AstronomyTool
from tools.ip_geolocation_tool import IPGeolocationTool
from tools.air_quality_tool import AirQualityTool
from tools.web_parser_tool import WebParserTool
from tools.time_tool import TimeTool
from tools.stock_tool import StockTool
from tools.geolocation_tool import GeolocationTool
from tools.news_tool import NewsTool

tools_to_test = [
    (AstronomyTool, 'astronomy_tool'),
    (IPGeolocationTool, 'ip_geolocation_tool'),
    (AirQualityTool, 'air_quality_tool'),
    (WebParserTool, 'web_parser_tool'),
    (TimeTool, 'time_tool'),
    (StockTool, 'stock_tool'),
    (GeolocationTool, 'geolocation_tool'),
    (NewsTool, 'news_tool'),
]

@pytest.mark.parametrize("tool_class, expected_name", tools_to_test)
def test_tool_metadata(tool_class, expected_name):
    """
    Smoke test: verify that the tool class can be instantiated and has TOOL_NAME and TOOL_DESCRIPTION.
    """
    tool = tool_class()
    assert hasattr(tool, 'TOOL_NAME'), f"{tool_class.__name__} missing TOOL_NAME"
    assert tool.TOOL_NAME == expected_name, f"Expected TOOL_NAME '{expected_name}', got '{tool.TOOL_NAME}'"
    assert hasattr(tool, 'TOOL_DESCRIPTION'), f"{tool_class.__name__} missing TOOL_DESCRIPTION"
    assert isinstance(tool.TOOL_DESCRIPTION, str) and tool.TOOL_DESCRIPTION, \
        f"TOOL_DESCRIPTION should be non-empty string" 