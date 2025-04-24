import os
import sys

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

print("Python path:", sys.path)
print("Current directory:", os.getcwd())
print("Parent directory:", parent_dir)

try:
    from tools.weather_tool import WeatherTool
    print("Successfully imported WeatherTool")
    
    # Try to create an instance
    tool = WeatherTool()
    print("Successfully created WeatherTool instance")
    
    # Try to use a method
    weather = tool.get_weather("London")
    print("Successfully got weather for London:", weather)
    
except Exception as e:
    print("Error:", str(e))
    import traceback
    traceback.print_exc() 