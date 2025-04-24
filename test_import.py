import sys
print("Python path:", sys.path)
print("Attempting to import tools...")
import tools
print("tools imported successfully")
print("Attempting to import weather_tool...")
from tools.weather_tool import WeatherTool
print("WeatherTool imported successfully") 