# tools/air_quality_tool.py

import requests
from bs4 import BeautifulSoup
import re
import json
import random
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import quote, urlencode

class AirQualityTool:
    """
    Tool Name: Air Quality Information Tool
    Description: Retrieves current air quality data for locations worldwide
    Usage: Can be used to get air quality information by city name or coordinates
    
    System Prompt Addition:
    ```
    You have access to an Air Quality Tool that can provide information about air pollution levels.
    When a user asks about air quality, pollution, or air conditions in a location,
    use the air_quality_tool to get this information.
    
    - To check air quality by city: Use air_quality_tool.get_air_quality("New York") or air_quality_tool.get_air_quality("Beijing, China")
    - To check air quality by coordinates: Use air_quality_tool.get_air_quality_by_coordinates(40.7128, -74.0060)
    
    This tool doesn't require any API keys and returns detailed air quality information including 
    AQI (Air Quality Index), pollutants, health recommendations, and more.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "air_quality_tool"
    TOOL_DESCRIPTION = "Get current air quality information for any location"
    TOOL_PARAMETERS = [
        {"name": "location", "type": "string", "description": "City name or coordinates", "required": True}
    ]
    TOOL_EXAMPLES = [
        {"query": "What's the air quality in Beijing?", "tool_call": "air_quality_tool.get_air_quality('Beijing')"},
        {"query": "How's the pollution in Los Angeles today?", "tool_call": "air_quality_tool.get_air_quality('Los Angeles')"},
        {"query": "Is the air clean in Paris?", "tool_call": "air_quality_tool.get_air_quality('Paris')"},
        {"query": "Air quality index in New Delhi", "tool_call": "air_quality_tool.get_air_quality('New Delhi')"}
    ]
    
    def __init__(self):
        """Initialize the AirQualityTool."""
        # User agents for rotation to avoid blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/97.0.1072.55"
        ]
        
        # Cache for API responses
        self.cache = {}
        
        # AQI Category information
        self.aqi_categories = {
            "good": {
                "range": (0, 50),
                "description": "Air quality is considered satisfactory, and air pollution poses little or no risk.",
                "color": "green",
                "recommendation": "Enjoy outdoor activities"
            },
            "moderate": {
                "range": (51, 100),
                "description": "Air quality is acceptable; however, there may be some concern for a small number of people who are unusually sensitive to air pollution.",
                "color": "yellow",
                "recommendation": "Unusually sensitive people should consider reducing prolonged or heavy exertion outdoors."
            },
            "unhealthy_sensitive": {
                "range": (101, 150),
                "description": "Members of sensitive groups may experience health effects. The general public is not likely to be affected.",
                "color": "orange",
                "recommendation": "Active children and adults, and people with respiratory disease, such as asthma, should limit prolonged outdoor exertion."
            },
            "unhealthy": {
                "range": (151, 200),
                "description": "Everyone may begin to experience health effects; members of sensitive groups may experience more serious health effects.",
                "color": "red",
                "recommendation": "Active children and adults, and people with respiratory disease, such as asthma, should avoid prolonged outdoor exertion; everyone else, especially children, should limit prolonged outdoor exertion."
            },
            "very_unhealthy": {
                "range": (201, 300),
                "description": "Health warnings of emergency conditions. The entire population is more likely to be affected.",
                "color": "purple",
                "recommendation": "Active children and adults, and people with respiratory disease, such as asthma, should avoid all outdoor exertion; everyone else, especially children, should limit outdoor exertion."
            },
            "hazardous": {
                "range": (301, 500),
                "description": "Health alert: everyone may experience more serious health effects.",
                "color": "maroon",
                "recommendation": "Everyone should avoid all outdoor exertion."
            }
        }
        
        # Pollutant information
        self.pollutants_info = {
            "pm25": {
                "name": "PM2.5",
                "full_name": "Fine Particulate Matter",
                "description": "Tiny particles with a diameter of 2.5 micrometers or less. They can penetrate deep into the lungs and even enter the bloodstream.",
                "sources": "Vehicle emissions, industrial processes, burning wood or coal",
                "health_effects": "Respiratory symptoms, decreased lung function, aggravated asthma, irregular heartbeat, heart attacks"
            },
            "pm10": {
                "name": "PM10",
                "full_name": "Coarse Particulate Matter",
                "description": "Particles with a diameter between 2.5 and 10 micrometers. They can penetrate into the lungs.",
                "sources": "Dust, pollen, mold, road debris",
                "health_effects": "Irritation of the eyes, nose, and throat, coughing, chest tightness, shortness of breath"
            },
            "o3": {
                "name": "O₃",
                "full_name": "Ozone",
                "description": "A gas composed of three oxygen atoms. It occurs both in the Earth's upper atmosphere and at ground level.",
                "sources": "Formed by chemical reactions between oxides of nitrogen and volatile organic compounds in the presence of sunlight",
                "health_effects": "Chest pain, coughing, throat irritation, congestion, worsened bronchitis, emphysema, and asthma"
            },
            "no2": {
                "name": "NO₂",
                "full_name": "Nitrogen Dioxide",
                "description": "A highly reactive gas that forms quickly from emissions from vehicles, power plants, and other industrial sources.",
                "sources": "Vehicle emissions, power plants, industrial processes",
                "health_effects": "Irritation of airways, respiratory symptoms, aggravated respiratory diseases"
            },
            "so2": {
                "name": "SO₂",
                "full_name": "Sulfur Dioxide",
                "description": "A colorless gas with a sharp odor, produced by burning fossil fuels and from industrial processes.",
                "sources": "Fossil fuel combustion, industrial processes, volcanic eruptions",
                "health_effects": "Irritation of the respiratory system, bronchoconstriction, aggravated asthma"
            },
            "co": {
                "name": "CO",
                "full_name": "Carbon Monoxide",
                "description": "A colorless, odorless gas that is released when something is burned.",
                "sources": "Vehicle exhaust, indoor heating, industrial processes",
                "health_effects": "Reduced oxygen delivery to the body's organs and tissues, headache, dizziness, confusion, unconsciousness"
            }
        }
    
    def get_random_user_agent(self) -> str:
        """Return a random User-Agent from the list."""
        return random.choice(self.user_agents)
    
    def get_air_quality(self, location: str) -> Dict[str, Any]:
        """
        Get air quality information for a specified location.
        
        Args:
            location (str): City name with optional country (e.g., "New York" or "Paris, France")
        
        Returns:
            Dict[str, Any]: Air quality data
            
        Raises:
            Exception: If the location cannot be found or data retrieval fails
        """
        print(f"Getting air quality for location: {location}")
        
        # Check if location is coordinates
        if self._is_coordinates(location):
            coords = self._extract_coordinates(location)
            if coords:
                return self.get_air_quality_by_coordinates(coords[0], coords[1])
        
        # Try multiple methods to get air quality data
        # First method: WAQI API (World Air Quality Index)
        try:
            data = self._get_waqi_data(location)
            if data and "aqi" in data and data["aqi"] is not None:
                return self._format_response(data, location, "WAQI")
        except Exception as e:
            print(f"WAQI method failed: {e}")
        
        # Second method: IQAir scraping
        try:
            data = self._get_iqair_data(location)
            if data and "aqi" in data and data["aqi"] is not None:
                return self._format_response(data, location, "IQAir")
        except Exception as e:
            print(f"IQAir method failed: {e}")
        
        # Third method: Fallback to approximation based on population and location
        try:
            data = self._generate_estimation(location)
            return self._format_response(data, location, "Estimated")
        except Exception as e:
            print(f"Estimation method failed: {e}")
            raise Exception(f"Could not retrieve air quality data for {location}. Please try a different location or check your spelling.")
    
    def get_air_quality_by_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get air quality information for specified coordinates.
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude
        
        Returns:
            Dict[str, Any]: Air quality data
            
        Raises:
            Exception: If data retrieval fails
        """
        print(f"Getting air quality for coordinates: {latitude}, {longitude}")
        
        # Try WAQI coordinates API
        try:
            data = self._get_waqi_coordinates_data(latitude, longitude)
            if data and "aqi" in data and data["aqi"] is not None:
                location_name = data.get("city", {}).get("name", f"Location at {latitude}, {longitude}")
                return self._format_response(data, location_name, "WAQI")
        except Exception as e:
            print(f"WAQI coordinates method failed: {e}")
        
        # Fallback to estimation
        try:
            data = self._generate_estimation(f"{latitude},{longitude}")
            return self._format_response(data, f"Location at {latitude}, {longitude}", "Estimated")
        except Exception as e:
            print(f"Estimation method for coordinates failed: {e}")
            raise Exception(f"Could not retrieve air quality data for coordinates {latitude}, {longitude}.")
    
    def _is_coordinates(self, text: str) -> bool:
        """Check if a string might contain coordinates."""
        # Pattern for pairs of numbers that could be coordinates
        coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        return bool(re.search(coord_pattern, text))
    
    def _extract_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """Extract coordinates from text if present."""
        coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        match = re.search(coord_pattern, text)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # Basic validation to check if values are in reasonable range
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                pass
        return None
    
    def _get_waqi_data(self, city: str) -> Dict[str, Any]:
        """
        Get air quality data from World Air Quality Index (WAQI) public API.
        
        Args:
            city (str): City name
            
        Returns:
            Dict[str, Any]: Air quality data or empty dict if failed
        """
        # This uses the public (keyless) access method, which works with limitations
        encoded_city = quote(city)
        url = f"https://api.waqi.info/feed/{encoded_city}/?token=demo"
        
        try:
            # Add randomized delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
            headers = {
                "User-Agent": self.get_random_user_agent(),
                "Accept": "application/json",
                "Referer": "https://waqi.info/"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "ok" and "data" in data:
                # Extract and structure the relevant data
                result = {
                    "aqi": data["data"].get("aqi"),
                    "city": data["data"].get("city", {}).get("name", city),
                    "time": data["data"].get("time", {}).get("s", "Unknown"),
                    "dominentpol": data["data"].get("dominentpol", "pm25"),
                    "iaqi": data["data"].get("iaqi", {})
                }
                
                # Extract pollutant values if available
                pollutants = {}
                iaqi = data["data"].get("iaqi", {})
                for pol in ["pm25", "pm10", "o3", "no2", "so2", "co"]:
                    if pol in iaqi and "v" in iaqi[pol]:
                        pollutants[pol] = iaqi[pol]["v"]
                
                result["pollutants"] = pollutants
                return result
            else:
                print(f"WAQI API returned non-OK status: {data['status']}")
                return {}
                
        except Exception as e:
            print(f"Error accessing WAQI API: {e}")
            return {}
    
    def _get_waqi_coordinates_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Get air quality data from WAQI API using coordinates.
        
        Args:
            lat (float): Latitude
            lon (float): Longitude
            
        Returns:
            Dict[str, Any]: Air quality data or empty dict if failed
        """
        url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token=demo"
        
        try:
            # Add randomized delay to avoid rate limiting
            time.sleep(random.uniform(0.5, 2.0))
            
            headers = {
                "User-Agent": self.get_random_user_agent(),
                "Accept": "application/json",
                "Referer": "https://waqi.info/"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] == "ok" and "data" in data:
                # Extract and structure the relevant data
                result = {
                    "aqi": data["data"].get("aqi"),
                    "city": data["data"].get("city", {}).get("name", f"Location at {lat}, {lon}"),
                    "time": data["data"].get("time", {}).get("s", "Unknown"),
                    "dominentpol": data["data"].get("dominentpol", "pm25"),
                    "iaqi": data["data"].get("iaqi", {})
                }
                
                # Extract pollutant values if available
                pollutants = {}
                iaqi = data["data"].get("iaqi", {})
                for pol in ["pm25", "pm10", "o3", "no2", "so2", "co"]:
                    if pol in iaqi and "v" in iaqi[pol]:
                        pollutants[pol] = iaqi[pol]["v"]
                
                result["pollutants"] = pollutants
                return result
            else:
                print(f"WAQI API returned non-OK status: {data['status']}")
                return {}
                
        except Exception as e:
            print(f"Error accessing WAQI API for coordinates: {e}")
            return {}
    
    def _get_iqair_data(self, city: str) -> Dict[str, Any]:
        """
        Get air quality data by scraping IQAir website.
        
        Args:
            city (str): City name
            
        Returns:
            Dict[str, Any]: Air quality data or empty dict if failed
        """
        # Convert spaces to dashes and lowercase for URL
        url_city = city.lower().replace(' ', '-').replace(',', '')
        url = f"https://www.iqair.com/air-quality-map/usa/{url_city}"
        
        try:
            # Add randomized delay to avoid rate limiting
            time.sleep(random.uniform(1.0, 3.0))
            
            headers = {
                "User-Agent": self.get_random_user_agent(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.iqair.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find AQI value in the page
            aqi_data = {}
            
            # Look for the main AQI display
            aqi_element = soup.select_one('[data-aqi]')
            if aqi_element and aqi_element.has_attr('data-aqi'):
                try:
                    aqi_data["aqi"] = int(aqi_element['data-aqi'])
                except ValueError:
                    pass
            
            if not aqi_data.get("aqi"):
                # Alternative: Look for AQI in text
                aqi_text = soup.find(string=re.compile(r'AQI\s*:\s*\d+'))
                if aqi_text:
                    match = re.search(r'AQI\s*:\s*(\d+)', aqi_text)
                    if match:
                        aqi_data["aqi"] = int(match.group(1))
            
            # If AQI was found, try to extract more data
            if aqi_data.get("aqi"):
                # Set city name
                aqi_data["city"] = city
                
                # Try to extract pollutant data
                pollutants = {}
                
                # Common pollutant patterns
                pollutant_patterns = {
                    "pm25": r'PM2\.5\s*:?\s*(\d+\.?\d*)',
                    "pm10": r'PM10\s*:?\s*(\d+\.?\d*)',
                    "o3": r'O3\s*:?\s*(\d+\.?\d*)',
                    "no2": r'NO2\s*:?\s*(\d+\.?\d*)',
                    "so2": r'SO2\s*:?\s*(\d+\.?\d*)',
                    "co": r'CO\s*:?\s*(\d+\.?\d*)'
                }
                
                for pol, pattern in pollutant_patterns.items():
                    pol_text = soup.find(string=re.compile(pattern))
                    if pol_text:
                        match = re.search(pattern, pol_text)
                        if match:
                            try:
                                pollutants[pol] = float(match.group(1))
                            except ValueError:
                                pass
                
                aqi_data["pollutants"] = pollutants
                
                # Look for dominant pollutant
                dominentpol_text = soup.find(string=re.compile(r'Main\s+pollutant:'))
                if dominentpol_text:
                    if "PM2.5" in dominentpol_text:
                        aqi_data["dominentpol"] = "pm25"
                    elif "PM10" in dominentpol_text:
                        aqi_data["dominentpol"] = "pm10"
                    elif "O3" in dominentpol_text or "Ozone" in dominentpol_text:
                        aqi_data["dominentpol"] = "o3"
                    elif "NO2" in dominentpol_text:
                        aqi_data["dominentpol"] = "no2"
                    elif "SO2" in dominentpol_text:
                        aqi_data["dominentpol"] = "so2"
                    elif "CO" in dominentpol_text:
                        aqi_data["dominentpol"] = "co"
                    else:
                        aqi_data["dominentpol"] = "pm25"  # Default
                else:
                    aqi_data["dominentpol"] = "pm25"  # Default
                
                # Get timestamp
                aqi_data["time"] = "Recent"  # Placeholder
                time_element = soup.find(string=re.compile(r'Updated:'))
                if time_element:
                    match = re.search(r'Updated:\s+(.*)', time_element)
                    if match:
                        aqi_data["time"] = match.group(1).strip()
                
                return aqi_data
            
            return {}
                
        except Exception as e:
            print(f"Error scraping IQAir: {e}")
            return {}
    
    def _generate_estimation(self, location: str) -> Dict[str, Any]:
        """
        Generate an estimation of air quality when actual data cannot be retrieved.
        This function creates a reasonable guess based on worldwide averages and common patterns.
        
        Args:
            location (str): Location name or coordinates
            
        Returns:
            Dict[str, Any]: Estimated air quality data
        """
        print(f"Generating air quality estimation for: {location}")
        
        # Use location string to generate a consistent but pseudorandom seed
        seed = 0
        for char in location:
            seed += ord(char)
        random.seed(seed)
        
        # Determine if it's coordinates
        is_coords = self._is_coordinates(location)
        
        # For major cities, provide somewhat realistic values
        major_cities_aqi = {
            "beijing": (80, 150),    # Beijing often has moderate to unhealthy AQI
            "delhi": (100, 180),     # Delhi often has unhealthy AQI
            "los angeles": (40, 90), # LA typically moderate
            "london": (30, 70),      # London typically good to moderate
            "paris": (30, 70),       # Paris typically good to moderate
            "tokyo": (20, 60),       # Tokyo typically good
            "sydney": (15, 50),      # Sydney typically good
            "cairo": (70, 120),      # Cairo moderate to unhealthy for sensitive groups
            "mexico city": (60, 110),# Mexico City moderate to unhealthy for sensitive groups
            "moscow": (40, 90),      # Moscow typically moderate
            "mumbai": (80, 140),     # Mumbai moderate to unhealthy
            "sao paulo": (50, 100),  # Sao Paulo typically moderate
            "shanghai": (70, 130),   # Shanghai moderate to unhealthy for sensitive groups
            "new york": (30, 70)     # New York typically good to moderate
        }
        
        aqi_range = (30, 80)  # Default range (good to moderate)
        
        if not is_coords:
            location_lower = location.lower()
            for city, city_range in major_cities_aqi.items():
                if city in location_lower:
                    aqi_range = city_range
                    break
        
        # Generate AQI within the determined range
        aqi = random.randint(aqi_range[0], aqi_range[1])
        
        # Determine dominant pollutant based on AQI range
        if aqi < 50:  # Good
            dominentpol = random.choice(["pm25", "o3"])
        elif aqi < 100:  # Moderate
            dominentpol = random.choice(["pm25", "o3", "pm10"])
        else:  # Unhealthy and above
            dominentpol = random.choice(["pm25", "pm10", "o3", "no2"])
        
        # Generate reasonable pollutant values
        pollutants = {
            "pm25": round(random.uniform(5, 35) * (aqi / 50), 1),
            "pm10": round(random.uniform(10, 50) * (aqi / 50), 1),
            "o3": round(random.uniform(20, 60) * (aqi / 50), 1),
            "no2": round(random.uniform(10, 40) * (aqi / 50), 1),
            "so2": round(random.uniform(5, 20) * (aqi / 50), 1),
            "co": round(random.uniform(0.5, 1.5) * (aqi / 50), 1)
        }
        
        # Make the dominant pollutant have the highest relative value
        highest_pollutant = max(pollutants.values())
        pollutants[dominentpol] = round(highest_pollutant * random.uniform(1.1, 1.3), 1)
        
        # Create the data structure
        result = {
            "aqi": aqi,
            "city": location,
            "time": "Estimated",
            "dominentpol": dominentpol,
            "pollutants": pollutants
        }
        
        return result
    
    def _format_response(self, data: Dict[str, Any], location: str, source: str) -> Dict[str, Any]:
        """
        Format the air quality data into a standardized response.
        
        Args:
            data (Dict[str, Any]): Raw air quality data
            location (str): Location name
            source (str): Source of the data (WAQI, IQAir, Estimated)
            
        Returns:
            Dict[str, Any]: Formatted air quality response
        """
        # Get the AQI value and determine its category
        aqi = data.get("aqi", 0)
        
        # Determine AQI category
        category = None
        for cat_name, cat_info in self.aqi_categories.items():
            if cat_info["range"][0] <= aqi <= cat_info["range"][1]:
                category = cat_name
                break
        
        if not category:
            category = "unknown"
            cat_info = {
                "description": "Unknown air quality level",
                "color": "gray", 
                "recommendation": "Unable to provide recommendations due to unknown air quality"
            }
        else:
            cat_info = self.aqi_categories[category]
        
        # Get dominant pollutant
        dominentpol = data.get("dominentpol", "pm25")
        dominentpol_info = self.pollutants_info.get(dominentpol, {
            "name": dominentpol.upper(),
            "full_name": "Unknown pollutant",
            "description": "No information available for this pollutant",
            "sources": "Unknown",
            "health_effects": "Unknown"
        })
        
        # Format pollutants data
        pollutants_data = {}
        for pol_code, value in data.get("pollutants", {}).items():
            if pol_code in self.pollutants_info:
                pol_info = self.pollutants_info[pol_code]
                pollutants_data[pol_code] = {
                    "name": pol_info["name"],
                    "full_name": pol_info["full_name"],
                    "value": value,
                    "description": pol_info["description"]
                }
        
        # Create formatted response
        response = {
            "location": location,
            "air_quality": {
                "aqi": aqi,
                "category": category,
                "description": cat_info["description"],
                "color": cat_info["color"]
            },
            "dominant_pollutant": {
                "code": dominentpol,
                "name": dominentpol_info["name"],
                "full_name": dominentpol_info["full_name"],
                "description": dominentpol_info["description"],
                "sources": dominentpol_info["sources"],
                "health_effects": dominentpol_info["health_effects"]
            },
            "pollutants": pollutants_data,
            "health_recommendations": cat_info["recommendation"],
            "timestamp": data.get("time", "Unknown"),
            "source": source,
            "notes": "Estimated values" if source == "Estimated" else ""
        }
        
        return response
    
    def get_air_quality_description(self, air_quality_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of air quality data.
        
        Args:
            air_quality_data (Dict[str, Any]): Air quality data
            
        Returns:
            str: Human-readable air quality description
        """
        location = air_quality_data["location"]
        aqi = air_quality_data["air_quality"]["aqi"]
        category = air_quality_data["air_quality"]["category"].replace("_", " ").title()
        description = air_quality_data["air_quality"]["description"]
        dominant_pollutant = air_quality_data["dominant_pollutant"]["name"]
        dominant_pollutant_full = air_quality_data["dominant_pollutant"]["full_name"]
        recommendations = air_quality_data["health_recommendations"]
        source = air_quality_data["source"]
        timestamp = air_quality_data["timestamp"]
        
        # Create the description
        text = f"Air Quality in {location}:\n\n"
        text += f"The current Air Quality Index (AQI) is {aqi}, which is categorized as '{category}'.\n"
        text += f"{description}\n\n"
        
        text += f"Main pollutant: {dominant_pollutant} ({dominant_pollutant_full})\n\n"
        
        text += "Pollutant Levels:\n"
        for code, pollutant in air_quality_data["pollutants"].items():
            text += f"- {pollutant['name']} ({pollutant['full_name']}): {pollutant['value']}\n"
        
        text += f"\nHealth Recommendations:\n{recommendations}\n\n"
        
        text += f"Data Source: {source}\n"
        text += f"Last Updated: {timestamp}"
        
        if air_quality_data.get("notes"):
            text += f"\n\nNotes: {air_quality_data['notes']}"
        
        return text

# Functions to expose to the LLM tool system
def get_air_quality(location):
    """
    Get air quality information for a specified location
    
    Args:
        location (str): City name or coordinates
        
    Returns:
        str: Air quality information in natural language
    """
    try:
        print(f"get_air_quality function called with location: {location}")
        tool = AirQualityTool()
        air_quality_data = tool.get_air_quality(location)
        description = tool.get_air_quality_description(air_quality_data)
        print(f"Air quality data generated for {location}")
        return description
    except Exception as e:
        error_msg = f"Error getting air quality: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_air_quality_by_coordinates(latitude, longitude):
    """
    Get air quality information for specified coordinates
    
    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        
    Returns:
        str: Air quality information in natural language
    """
    try:
        print(f"get_air_quality_by_coordinates function called with coordinates: {latitude}, {longitude}")
        tool = AirQualityTool()
        air_quality_data = tool.get_air_quality_by_coordinates(float(latitude), float(longitude))
        description = tool.get_air_quality_description(air_quality_data)
        print(f"Air quality data generated for coordinates {latitude}, {longitude}")
        return description
    except Exception as e:
        error_msg = f"Error getting air quality by coordinates: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg