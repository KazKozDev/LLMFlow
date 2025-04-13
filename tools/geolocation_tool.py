# tools/geolocation_tool.py

import requests
import json
import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import re
from urllib.parse import quote

class GeolocationTool:
    """
    Tool Name: Geolocation Information Tool
    Description: Provides geographic information about locations, distances, and points of interest
    Usage: Can be used to geocode places, find distances, and discover nearby locations
    
    System Prompt Addition:
    ```
    You have access to a Geolocation Tool that can provide geographic information about places.
    When a user asks about locations, addresses, distances between places, or nearby points of interest,
    use the geolocation_tool to get this information.
    
    - To get info about a location: Use geolocation_tool.get_location_info("Paris, France")
    - To get info from coordinates: Use geolocation_tool.get_location_from_coordinates(48.8566, 2.3522)
    - To calculate distance: Use geolocation_tool.calculate_distance("New York", "Los Angeles")
    - To find nearby places: Use geolocation_tool.find_nearby_places("Tokyo", "restaurants")
    
    This tool doesn't require any API keys and returns detailed geographic information including
    coordinates, address components, nearby points of interest, and distance calculations.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "geolocation_tool"
    TOOL_DESCRIPTION = "Get geographical information about locations, distances, and nearby points of interest"
    TOOL_PARAMETERS = [
        {"name": "location", "type": "string", "description": "Place name, address or coordinates", "required": True},
        {"name": "secondary_location", "type": "string", "description": "Second location for distance calculations or category for nearby search", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "Where is the Eiffel Tower located?", "tool_call": "geolocation_tool.get_location_info('Eiffel Tower, Paris')"},
        {"query": "What's the distance between London and Edinburgh?", "tool_call": "geolocation_tool.calculate_distance('London', 'Edinburgh')"},
        {"query": "Show me restaurants near Times Square", "tool_call": "geolocation_tool.find_nearby_places('Times Square, New York', 'restaurants')"},
        {"query": "Какие достопримечательности рядом с Красной площадью?", "tool_call": "geolocation_tool.find_nearby_places('Red Square, Moscow', 'attractions')"}
    ]
    
    def __init__(self):
        """Initialize the GeolocationTool with free API endpoints."""
        # Nominatim API for OpenStreetMap (geocoding)
        self.geocoding_url = "https://nominatim.openstreetmap.org/search"
        # Reverse geocoding API
        self.reverse_geocoding_url = "https://nominatim.openstreetmap.org/reverse"
        # Overpass API for nearby places
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        # User agent required by Nominatim
        self.headers = {
            'User-Agent': 'GeolocationToolForLLM/1.0'
        }
        # Cache for API responses
        self.location_cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (1 hour)
        self.cache_expiry = 3600
        # Earth radius in kilometers (for distance calculations)
        self.earth_radius = 6371.0
    
    def get_location_info(self, location: str) -> Dict[str, Any]:
        """
        Get detailed information about a location by name.
        
        Args:
            location (str): Place name, address, or landmark
        
        Returns:
            Dict[str, Any]: Detailed information about the location
            
        Raises:
            Exception: If the API request fails or location not found
        """
        print(f"Getting location info for: {location}")
        
        # Check if the input might be coordinates
        coords = self._parse_coordinates(location)
        if coords:
            return self.get_location_from_coordinates(coords[0], coords[1])
        
        # Check cache
        cache_key = f"location:{location}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.location_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached location data for {location}")
            return self.location_cache[cache_key]
        
        # Prepare request parameters
        params = {
            'q': location,
            'format': 'json',
            'addressdetails': 1,
            'extratags': 1,
            'namedetails': 1,
            'limit': 1
        }
        
        try:
            print(f"Making geocoding request for: {location}")
            response = requests.get(
                self.geocoding_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"Received response for {location}")
            
            if not data:
                raise Exception(f"Location '{location}' not found")
            
            # Format the response
            location_data = self._format_location_data(data[0])
            
            # Cache the result
            self.location_cache[cache_key] = location_data
            self.cache_timestamp[cache_key] = current_time
            
            return location_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error in geocoding request: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error getting location info: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get_location_from_coordinates(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get location information from coordinates (reverse geocoding).
        
        Args:
            latitude (float): Latitude
            longitude (float): Longitude
        
        Returns:
            Dict[str, Any]: Detailed information about the location
            
        Raises:
            Exception: If the API request fails
        """
        print(f"Getting location from coordinates: {latitude}, {longitude}")
        
        # Check cache
        cache_key = f"reverse:{latitude},{longitude}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.location_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached reverse geocoding data")
            return self.location_cache[cache_key]
        
        # Prepare request parameters
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'addressdetails': 1,
            'extratags': 1,
            'namedetails': 1
        }
        
        try:
            print(f"Making reverse geocoding request")
            response = requests.get(
                self.reverse_geocoding_url, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"Received reverse geocoding response")
            
            # Format the response
            location_data = self._format_location_data(data)
            
            # Cache the result
            self.location_cache[cache_key] = location_data
            self.cache_timestamp[cache_key] = current_time
            
            return location_data
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error in reverse geocoding request: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error getting location from coordinates: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def calculate_distance(self, location1: str, location2: str) -> Dict[str, Any]:
        """
        Calculate the distance between two locations.
        
        Args:
            location1 (str): First location name or address
            location2 (str): Second location name or address
        
        Returns:
            Dict[str, Any]: Distance information
            
        Raises:
            Exception: If locations cannot be found or calculation fails
        """
        print(f"Calculating distance between: {location1} and {location2}")
        
        # Check cache
        cache_key = f"distance:{location1}|{location2}"
        reversed_cache_key = f"distance:{location2}|{location1}"
        current_time = datetime.now().timestamp()
        
        if cache_key in self.location_cache and current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry:
            print(f"Using cached distance data")
            return self.location_cache[cache_key]
        elif reversed_cache_key in self.location_cache and current_time - self.cache_timestamp.get(reversed_cache_key, 0) < self.cache_expiry:
            print(f"Using cached reversed distance data")
            return self.location_cache[reversed_cache_key]
        
        try:
            # Get coordinates for both locations
            location1_data = self.get_location_info(location1)
            location2_data = self.get_location_info(location2)
            
            # Extract coordinates
            lat1 = float(location1_data["coordinates"]["latitude"])
            lon1 = float(location1_data["coordinates"]["longitude"])
            lat2 = float(location2_data["coordinates"]["latitude"])
            lon2 = float(location2_data["coordinates"]["longitude"])
            
            # Calculate distance using the Haversine formula
            distance_km = self._haversine_distance(lat1, lon1, lat2, lon2)
            distance_miles = distance_km * 0.621371
            
            # Format the response
            result = {
                "locations": {
                    "origin": {
                        "query": location1,
                        "formatted_address": location1_data["formatted_address"],
                        "coordinates": location1_data["coordinates"]
                    },
                    "destination": {
                        "query": location2,
                        "formatted_address": location2_data["formatted_address"],
                        "coordinates": location2_data["coordinates"]
                    }
                },
                "distance": {
                    "kilometers": round(distance_km, 2),
                    "miles": round(distance_miles, 2),
                    "formatted": f"{round(distance_km, 2)} km ({round(distance_miles, 2)} miles)"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.location_cache[cache_key] = result
            self.cache_timestamp[cache_key] = current_time
            
            return result
            
        except Exception as e:
            error_msg = f"Error calculating distance: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def find_nearby_places(self, location: str, category: str, radius_km: float = 2.0) -> Dict[str, Any]:
        """
        Find places of interest near a location.
        
        Args:
            location (str): Center location name or address
            category (str): Category of places to find (e.g., restaurants, attractions)
            radius_km (float, optional): Search radius in kilometers (default: 2.0)
        
        Returns:
            Dict[str, Any]: Nearby places information
            
        Raises:
            Exception: If the location cannot be found or search fails
        """
        print(f"Finding {category} near {location} within {radius_km}km")
        
        # Normalize category
        category = self._normalize_category(category)
        
        # Check cache
        cache_key = f"nearby:{location}|{category}|{radius_km}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.location_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached nearby places data")
            return self.location_cache[cache_key]
        
        try:
            # Get coordinates for the location
            location_data = self.get_location_info(location)
            latitude = float(location_data["coordinates"]["latitude"])
            longitude = float(location_data["coordinates"]["longitude"])
            
            # Convert category to OSM tags
            osm_tags = self._category_to_osm_tags(category)
            
            # Prepare Overpass query
            overpass_query = self._build_overpass_query(latitude, longitude, radius_km, osm_tags)
            
            # Execute query
            response = requests.post(
                self.overpass_url,
                data={"data": overpass_query},
                headers=self.headers,
                timeout=15
            )
            response.raise_for_status()
            
            # Parse results
            places = self._parse_overpass_results(response.json(), category)
            
            # Add distance from center for each place
            for place in places:
                place_lat = float(place["coordinates"]["latitude"])
                place_lon = float(place["coordinates"]["longitude"])
                distance = self._haversine_distance(latitude, longitude, place_lat, place_lon)
                place["distance"] = {
                    "kilometers": round(distance, 2),
                    "miles": round(distance * 0.621371, 2)
                }
            
            # Sort by distance
            places.sort(key=lambda x: x["distance"]["kilometers"])
            
            # Limit to 10 places
            places = places[:10]
            
            # Format the result
            result = {
                "center": {
                    "query": location,
                    "formatted_address": location_data["formatted_address"],
                    "coordinates": location_data["coordinates"]
                },
                "category": category,
                "radius_km": radius_km,
                "count": len(places),
                "places": places,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache the result
            self.location_cache[cache_key] = result
            self.cache_timestamp[cache_key] = current_time
            
            return result
            
        except Exception as e:
            error_msg = f"Error finding nearby places: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _format_location_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format raw API response into a standardized location data object.
        
        Args:
            raw_data (Dict[str, Any]): Raw API response
            
        Returns:
            Dict[str, Any]: Formatted location data
        """
        # Extract coordinates
        latitude = float(raw_data.get("lat", 0))
        longitude = float(raw_data.get("lon", 0))
        
        # Extract address components
        address = raw_data.get("address", {})
        
        # Construct formatted address
        address_parts = []
        for key in ["road", "house_number", "neighbourhood", "suburb", "city", "town", "village", 
                    "municipality", "county", "state", "country"]:
            if key in address and address[key]:
                address_parts.append(address[key])
        
        formatted_address = ", ".join(filter(None, address_parts))
        if not formatted_address and "display_name" in raw_data:
            formatted_address = raw_data["display_name"]
        
        # Extract place type and name
        place_type = raw_data.get("type", "unknown")
        place_name = raw_data.get("name", "")
        if not place_name and "namedetails" in raw_data and "name" in raw_data["namedetails"]:
            place_name = raw_data["namedetails"]["name"]
        if not place_name and "display_name" in raw_data:
            place_name = raw_data["display_name"].split(",")[0]
        
        # Extract extra tags if available
        extra_info = {}
        if "extratags" in raw_data:
            extra_tags = raw_data["extratags"]
            if "website" in extra_tags:
                extra_info["website"] = extra_tags["website"]
            if "phone" in extra_tags:
                extra_info["phone"] = extra_tags["phone"]
            if "opening_hours" in extra_tags:
                extra_info["opening_hours"] = extra_tags["opening_hours"]
            if "cuisine" in extra_tags:
                extra_info["cuisine"] = extra_tags["cuisine"]
            if "wikipedia" in extra_tags:
                extra_info["wikipedia"] = extra_tags["wikipedia"]
            if "description" in extra_tags:
                extra_info["description"] = extra_tags["description"]
            if "wikidata" in extra_tags:
                extra_info["wikidata"] = extra_tags["wikidata"]
        
        # Construct the result
        result = {
            "name": place_name,
            "type": place_type,
            "formatted_address": formatted_address,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "address_components": {
                "country": address.get("country", ""),
                "country_code": address.get("country_code", "").upper(),
                "state": address.get("state", ""),
                "county": address.get("county", ""),
                "city": address.get("city", address.get("town", address.get("village", ""))),
                "district": address.get("suburb", address.get("neighbourhood", "")),
                "street": address.get("road", ""),
                "house_number": address.get("house_number", ""),
                "postcode": address.get("postcode", "")
            },
            "osm_id": raw_data.get("osm_id", ""),
            "osm_type": raw_data.get("osm_type", ""),
            "extra_info": extra_info
        }
        
        return result
    
    def _parse_coordinates(self, text: str) -> Optional[Tuple[float, float]]:
        """
        Parse coordinates from text input.
        
        Args:
            text (str): Text that might contain coordinates
            
        Returns:
            Optional[Tuple[float, float]]: Tuple of (latitude, longitude) or None if not found
        """
        # Pattern for decimal degrees: "latitude, longitude" or "latitude longitude"
        decimal_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        
        match = re.search(decimal_pattern, text)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # Basic validation
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            except ValueError:
                pass
        
        return None
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two points using the Haversine formula.
        
        Args:
            lat1 (float): Latitude of first point in decimal degrees
            lon1 (float): Longitude of first point in decimal degrees
            lat2 (float): Latitude of second point in decimal degrees
            lon2 (float): Longitude of second point in decimal degrees
            
        Returns:
            float: Distance in kilometers
        """
        # Convert decimal degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = self.earth_radius * c
        
        return distance
    
    def _normalize_category(self, category: str) -> str:
        """
        Normalize the category input to match known categories.
        
        Args:
            category (str): User-provided category
            
        Returns:
            str: Normalized category
        """
        category = category.lower().strip()
        
        # Map common categories to normalized values
        category_mapping = {
            # Food and drinks
            "restaurant": "restaurants",
            "restaurants": "restaurants",
            "cafe": "cafes",
            "cafes": "cafes",
            "bar": "bars",
            "bars": "bars",
            "pub": "pubs",
            "pubs": "pubs",
            "food": "restaurants",
            "dining": "restaurants",
            "fastfood": "fast_food",
            "fast food": "fast_food",
            "fast-food": "fast_food",
            "coffee": "cafes",
            "pizza": "restaurants",
            "sushi": "restaurants",
            
            # Attractions and entertainment
            "attraction": "attractions",
            "attractions": "attractions",
            "landmark": "attractions",
            "landmarks": "attractions",
            "sightseeing": "attractions",
            "tourism": "attractions",
            "tourist": "attractions",
            "museum": "museums",
            "museums": "museums",
            "gallery": "museums",
            "galleries": "museums",
            "art": "museums",
            "historical": "attractions",
            "history": "museums",
            "monument": "attractions",
            "monuments": "attractions",
            "park": "parks",
            "parks": "parks",
            "garden": "parks",
            "gardens": "parks",
            "theater": "entertainment",
            "theatre": "entertainment",
            "cinema": "entertainment",
            "movie": "entertainment",
            "movies": "entertainment",
            
            # Accommodation
            "hotel": "hotels",
            "hotels": "hotels",
            "hostel": "hotels",
            "hostels": "hotels",
            "motel": "hotels",
            "motels": "hotels",
            "accommodation": "hotels",
            "lodging": "hotels",
            
            # Shopping
            "shop": "shopping",
            "shopping": "shopping",
            "store": "shopping",
            "stores": "shopping",
            "mall": "shopping",
            "malls": "shopping",
            "supermarket": "shopping",
            "supermarkets": "shopping",
            "market": "shopping",
            "markets": "shopping",
            
            # Transportation
            "station": "transit",
            "stations": "transit",
            "transit": "transit",
            "transport": "transit",
            "transportation": "transit",
            "bus": "transit",
            "train": "transit",
            "subway": "transit",
            "metro": "transit",
            "airport": "transit",
            "taxi": "transit",
            
            # Services
            "bank": "services",
            "banks": "services",
            "atm": "services",
            "hospital": "healthcare",
            "hospitals": "healthcare",
            "clinic": "healthcare",
            "clinics": "healthcare",
            "doctor": "healthcare",
            "pharmacy": "healthcare",
            "pharmacies": "healthcare",
            "healthcare": "healthcare",
            "health": "healthcare",
            "police": "services",
            "post": "services",
            "postal": "services",
            
            # Other common categories
            "gas": "gas_stations",
            "gas station": "gas_stations",
            "gas stations": "gas_stations",
            "petrol": "gas_stations",
            "fuel": "gas_stations",
            "school": "education",
            "schools": "education",
            "university": "education",
            "college": "education",
            "education": "education",
            "church": "religious",
            "religious": "religious",
            "temple": "religious",
            "mosque": "religious",
            "synagogue": "religious",
            "gym": "fitness",
            "fitness": "fitness",
            "sport": "sports",
            "sports": "sports"
        }
        
        # Translate Russian categories (basic support)
        russian_mapping = {
            "ресторан": "restaurants",
            "рестораны": "restaurants",
            "кафе": "cafes",
            "бар": "bars",
            "бары": "bars",
            "паб": "pubs",
            "пабы": "pubs",
            "еда": "restaurants",
            "достопримечательность": "attractions",
            "достопримечательности": "attractions",
            "музей": "museums",
            "музеи": "museums",
            "галерея": "museums",
            "галереи": "museums",
            "искусство": "museums",
            "парк": "parks",
            "парки": "parks",
            "сад": "parks",
            "сады": "parks",
            "театр": "entertainment",
            "кино": "entertainment",
            "отель": "hotels",
            "гостиница": "hotels",
            "магазин": "shopping",
            "магазины": "shopping",
            "торговый центр": "shopping",
            "супермаркет": "shopping",
            "рынок": "shopping"
        }
        
        # Try to find the normalized category
        if category in category_mapping:
            return category_mapping[category]
        elif category in russian_mapping:
            return russian_mapping[category]
        else:
            # Check for partial matches
            for key, value in category_mapping.items():
                if key in category or category in key:
                    return value
        
        # Default to generic "points of interest" if unknown
        return "points_of_interest"
    
    def _category_to_osm_tags(self, category: str) -> Dict[str, List[str]]:
        """
        Convert a category to OpenStreetMap tags for Overpass API.
        
        Args:
            category (str): Normalized category
            
        Returns:
            Dict[str, List[str]]: Dictionary with tag types and values
        """
        # Map categories to OSM tags
        osm_tags = {
            "restaurants": {
                "amenity": ["restaurant", "fast_food", "food_court"],
                "cuisine": []
            },
            "cafes": {
                "amenity": ["cafe", "coffee_shop"],
                "shop": ["coffee"]
            },
            "bars": {
                "amenity": ["bar", "pub", "biergarten"]
            },
            "pubs": {
                "amenity": ["pub"]
            },
            "fast_food": {
                "amenity": ["fast_food"]
            },
            "attractions": {
                "tourism": ["attraction", "viewpoint", "artwork", "gallery"],
                "historic": ["monument", "memorial", "ruins", "archaeological_site", "castle", "fort"]
            },
            "museums": {
                "tourism": ["museum", "gallery"],
                "amenity": ["arts_centre"]
            },
            "parks": {
                "leisure": ["park", "garden", "nature_reserve"],
                "tourism": ["zoo"]
            },
            "entertainment": {
                "amenity": ["theatre", "cinema", "nightclub", "arts_centre"],
                "leisure": ["amusement_arcade", "bowling_alley"]
            },
            "hotels": {
                "tourism": ["hotel", "hostel", "motel", "guest_house", "apartment"]
            },
            "shopping": {
                "shop": ["mall", "supermarket", "department_store", "convenience", "clothes", "electronics"],
                "amenity": ["marketplace"]
            },
            "transit": {
                "amenity": ["bus_station"],
                "public_transport": ["station", "stop_position"],
                "railway": ["station", "halt"],
                "aeroway": ["aerodrome", "terminal"]
            },
            "services": {
                "amenity": ["bank", "atm", "post_office", "police", "fire_station", "townhall", "library"]
            },
            "healthcare": {
                "amenity": ["hospital", "clinic", "doctors", "dentist", "pharmacy"]
            },
            "gas_stations": {
                "amenity": ["fuel", "charging_station"]
            },
            "education": {
                "amenity": ["school", "university", "college", "kindergarten", "library"]
            },
            "religious": {
                "amenity": ["place_of_worship"],
                "building": ["church", "mosque", "temple", "synagogue", "cathedral"]
            },
            "fitness": {
                "leisure": ["fitness_centre", "sports_centre", "swimming_pool"]
            },
            "sports": {
                "leisure": ["sports_centre", "stadium", "pitch", "track"]
            },
            "points_of_interest": {
                "tourism": ["attraction", "viewpoint", "museum", "gallery", "artwork"],
                "amenity": ["restaurant", "cafe", "bar", "theatre", "cinema"],
                "leisure": ["park", "garden"]
            }
        }
        
        return osm_tags.get(category, osm_tags["points_of_interest"])
    
    def _build_overpass_query(self, lat: float, lon: float, radius_km: float, osm_tags: Dict[str, List[str]]) -> str:
        """
        Build an Overpass QL query to find places of a given category near coordinates.
        
        Args:
            lat (float): Latitude of center point
            lon (float): Longitude of center point
            radius_km (float): Search radius in kilometers
            osm_tags (Dict[str, List[str]]): OSM tags to search for
            
        Returns:
            str: Overpass QL query
        """
        # Convert radius to meters
        radius_m = radius_km * 1000
        
        # Build the query
        query = f"""
        [out:json][timeout:25];
        (
        """
        
        # Add node queries for each tag type
        for tag_type, tag_values in osm_tags.items():
            for value in tag_values:
                query += f"""
                node["{tag_type}"="{value}"](around:{radius_m},{lat},{lon});
                way["{tag_type}"="{value}"](around:{radius_m},{lat},{lon});
                relation["{tag_type}"="{value}"](around:{radius_m},{lat},{lon});
                """
        
        # Close the query
        query += f"""
        );
        out body;
        >;
        out skel qt;
        """
        
        return query
    
    def _parse_overpass_results(self, data: Dict[str, Any], category: str) -> List[Dict[str, Any]]:
        """
        Parse Overpass API results into a list of places.
        
        Args:
            data (Dict[str, Any]): Overpass API response
            category (str): The category that was searched for
            
        Returns:
            List[Dict[str, Any]]: List of place objects
        """
        places = []
        
        # Process each element in the results
        elements = data.get("elements", [])
        
        for element in elements:
            # Only process nodes (points) and ways (areas) with tags
            if "tags" not in element or element.get("type") not in ["node", "way"]:
                continue
                
            tags = element["tags"]
            
            # Skip elements without a name
            if "name" not in tags:
                continue
                
            # Get basic place info
            place_name = tags.get("name", "Unnamed Place")
            
            # Skip place if already in results (by name)
            if any(p["name"] == place_name for p in places):
                continue
                
            # Get coordinates
            if element["type"] == "node":
                lat = element.get("lat", 0)
                lon = element.get("lon", 0)
            else:  # For ways, use the center point if available
                center = self._get_way_center(element, data)
                if not center:
                    continue
                lat, lon = center
            
            # Build address components from available tags
            address_components = {
                "country": tags.get("addr:country", ""),
                "city": tags.get("addr:city", ""),
                "street": tags.get("addr:street", ""),
                "house_number": tags.get("addr:housenumber", "")
            }
            
            # Build extra info
            extra_info = {}
            if "website" in tags:
                extra_info["website"] = tags["website"]
            if "phone" in tags:
                extra_info["phone"] = tags["phone"]
            if "opening_hours" in tags:
                extra_info["opening_hours"] = tags["opening_hours"]
            if "cuisine" in tags:
                extra_info["cuisine"] = tags["cuisine"]
            if "description" in tags:
                extra_info["description"] = tags["description"]
            
            # Create place object
            place = {
                "name": place_name,
                "type": self._get_place_type(tags, category),
                "coordinates": {
                    "latitude": lat,
                    "longitude": lon
                },
                "address_components": address_components,
                "osm_id": element.get("id", ""),
                "osm_type": element.get("type", ""),
                "extra_info": extra_info
            }
            
            places.append(place)
        
        return places
    
    def _get_way_center(self, way: Dict[str, Any], data: Dict[str, Any]) -> Optional[Tuple[float, float]]:
        """
        Calculate the center point of a way (polygon) from Overpass data.
        
        Args:
            way (Dict[str, Any]): Way element data
            data (Dict[str, Any]): Complete Overpass response
            
        Returns:
            Optional[Tuple[float, float]]: Center coordinates (lat, lon) or None
        """
        if "center" in way:
            return (way["center"]["lat"], way["center"]["lon"])
            
        if "nodes" not in way:
            return None
            
        # Find node elements
        nodes = {}
        for element in data.get("elements", []):
            if element.get("type") == "node" and "id" in element:
                nodes[element["id"]] = element
        
        # Calculate average of node coordinates
        coords = []
        for node_id in way["nodes"]:
            if node_id in nodes and "lat" in nodes[node_id] and "lon" in nodes[node_id]:
                coords.append((nodes[node_id]["lat"], nodes[node_id]["lon"]))
        
        if not coords:
            return None
            
        avg_lat = sum(c[0] for c in coords) / len(coords)
        avg_lon = sum(c[1] for c in coords) / len(coords)
        
        return (avg_lat, avg_lon)
    
    def _get_place_type(self, tags: Dict[str, str], category: str) -> str:
        """
        Determine the place type from OSM tags.
        
        Args:
            tags (Dict[str, str]): OSM tags
            category (str): Search category
            
        Returns:
            str: Human-readable place type
        """
        # Map common OSM tags to readable place types
        if "amenity" in tags:
            amenity = tags["amenity"]
            if amenity == "restaurant":
                return "Restaurant"
            elif amenity == "cafe":
                return "Cafe"
            elif amenity == "bar":
                return "Bar"
            elif amenity == "pub":
                return "Pub"
            elif amenity == "fast_food":
                return "Fast Food"
            elif amenity == "cinema":
                return "Cinema"
            elif amenity == "theatre":
                return "Theatre"
            elif amenity == "bank":
                return "Bank"
            elif amenity == "hospital":
                return "Hospital"
            elif amenity == "pharmacy":
                return "Pharmacy"
            elif amenity == "fuel":
                return "Gas Station"
            elif amenity == "school":
                return "School"
            elif amenity == "university":
                return "University"
            elif amenity == "place_of_worship":
                return "Place of Worship"
            
        if "tourism" in tags:
            tourism = tags["tourism"]
            if tourism == "hotel":
                return "Hotel"
            elif tourism == "attraction":
                return "Tourist Attraction"
            elif tourism == "museum":
                return "Museum"
            elif tourism == "gallery":
                return "Art Gallery"
        
        if "shop" in tags:
            shop = tags["shop"]
            if shop == "supermarket":
                return "Supermarket"
            elif shop == "mall":
                return "Shopping Mall"
            elif shop == "clothes":
                return "Clothing Store"
        
        if "leisure" in tags:
            leisure = tags["leisure"]
            if leisure == "park":
                return "Park"
            elif leisure == "garden":
                return "Garden"
            elif leisure == "fitness_centre":
                return "Fitness Center"
        
        # Fallback to the category if no specific type is found
        category_types = {
            "restaurants": "Restaurant",
            "cafes": "Cafe",
            "bars": "Bar",
            "pubs": "Pub",
            "attractions": "Attraction",
            "museums": "Museum",
            "parks": "Park",
            "entertainment": "Entertainment Venue",
            "hotels": "Accommodation",
            "shopping": "Shop",
            "transit": "Transportation",
            "services": "Service",
            "healthcare": "Healthcare Facility",
            "gas_stations": "Gas Station",
            "education": "Educational Institution",
            "religious": "Religious Building",
            "fitness": "Fitness Venue",
            "sports": "Sports Venue"
        }
        
        return category_types.get(category, "Place of Interest")
    
    def get_location_description(self, location_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of a location.
        
        Args:
            location_data (Dict[str, Any]): Location data from get_location_info
            
        Returns:
            str: Human-readable location description
        """
        name = location_data["name"]
        formatted_address = location_data["formatted_address"]
        lat = location_data["coordinates"]["latitude"]
        lon = location_data["coordinates"]["longitude"]
        
        extra_info = location_data.get("extra_info", {})
        description = extra_info.get("description", "")
        
        text = f"{name} is located at {formatted_address}.\n"
        text += f"Coordinates: {lat}, {lon}\n"
        
        if description:
            text += f"\nDescription: {description}\n"
        
        # Add country, state, city info if available
        components = location_data["address_components"]
        location_parts = []
        
        if components.get("city"):
            location_parts.append(f"City: {components['city']}")
        if components.get("state"):
            location_parts.append(f"State/Region: {components['state']}")
        if components.get("country"):
            location_parts.append(f"Country: {components['country']}")
        
        if location_parts:
            text += "\n" + "\n".join(location_parts)
        
        # Add extra information if available
        extra_parts = []
        if "website" in extra_info:
            extra_parts.append(f"Website: {extra_info['website']}")
        if "phone" in extra_info:
            extra_parts.append(f"Phone: {extra_info['phone']}")
        if "opening_hours" in extra_info:
            extra_parts.append(f"Opening Hours: {extra_info['opening_hours']}")
        
        if extra_parts:
            text += "\n\nAdditional Information:\n" + "\n".join(extra_parts)
        
        return text
    
    def get_distance_description(self, distance_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of distance calculation.
        
        Args:
            distance_data (Dict[str, Any]): Distance data from calculate_distance
            
        Returns:
            str: Human-readable distance description
        """
        origin = distance_data["locations"]["origin"]["formatted_address"]
        destination = distance_data["locations"]["destination"]["formatted_address"]
        distance_km = distance_data["distance"]["kilometers"]
        distance_miles = distance_data["distance"]["miles"]
        
        text = f"The distance between {origin} and {destination} is {distance_km} kilometers ({distance_miles} miles)."
        
        # Add coordinates
        origin_lat = distance_data["locations"]["origin"]["coordinates"]["latitude"]
        origin_lon = distance_data["locations"]["origin"]["coordinates"]["longitude"]
        dest_lat = distance_data["locations"]["destination"]["coordinates"]["latitude"]
        dest_lon = distance_data["locations"]["destination"]["coordinates"]["longitude"]
        
        text += f"\n\nCoordinates:"
        text += f"\nOrigin: {origin_lat}, {origin_lon}"
        text += f"\nDestination: {dest_lat}, {dest_lon}"
        
        return text
    
    def get_nearby_places_description(self, nearby_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of nearby places.
        
        Args:
            nearby_data (Dict[str, Any]): Nearby places data from find_nearby_places
            
        Returns:
            str: Human-readable nearby places description
        """
        center = nearby_data["center"]["formatted_address"]
        category = nearby_data["category"]
        radius = nearby_data["radius_km"]
        count = nearby_data["count"]
        places = nearby_data["places"]
        
        text = f"Found {count} {category} within {radius} km of {center}:\n\n"
        
        if count == 0:
            text = f"No {category} found within {radius} km of {center}."
            return text
        
        for i, place in enumerate(places):
            name = place["name"]
            distance_km = place["distance"]["kilometers"]
            distance_miles = place["distance"]["miles"]
            place_type = place["type"]
            
            text += f"{i+1}. {name} ({place_type})\n"
            text += f"   Distance: {distance_km} km ({distance_miles} miles)\n"
            
            extra_info = place.get("extra_info", {})
            if "opening_hours" in extra_info:
                text += f"   Hours: {extra_info['opening_hours']}\n"
            if "cuisine" in extra_info and category == "restaurants":
                text += f"   Cuisine: {extra_info['cuisine']}\n"
            
            text += "\n"
        
        return text

# Functions to expose to the LLM tool system
def get_location_info(location):
    """
    Get detailed information about a location by name
    
    Args:
        location (str): Place name, address, or landmark
        
    Returns:
        str: Location information in natural language
    """
    try:
        print(f"get_location_info function called with location: {location}")
        tool = GeolocationTool()
        location_data = tool.get_location_info(location)
        description = tool.get_location_description(location_data)
        print(f"Location description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting location info: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_location_from_coordinates(latitude, longitude):
    """
    Get location information from coordinates (reverse geocoding)
    
    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        
    Returns:
        str: Location information in natural language
    """
    try:
        print(f"get_location_from_coordinates function called with coords: {latitude}, {longitude}")
        tool = GeolocationTool()
        location_data = tool.get_location_from_coordinates(float(latitude), float(longitude))
        description = tool.get_location_description(location_data)
        print(f"Location description generated from coordinates")
        return description
    except Exception as e:
        error_msg = f"Error getting location from coordinates: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def calculate_distance(location1, location2):
    """
    Calculate the distance between two locations
    
    Args:
        location1 (str): First location name or address
        location2 (str): Second location name or address
        
    Returns:
        str: Distance information in natural language
    """
    try:
        print(f"calculate_distance function called between: {location1} and {location2}")
        tool = GeolocationTool()
        distance_data = tool.calculate_distance(location1, location2)
        description = tool.get_distance_description(distance_data)
        print(f"Distance calculation completed")
        return description
    except Exception as e:
        error_msg = f"Error calculating distance: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def find_nearby_places(location, category, radius_km=2.0):
    """
    Find places of interest near a location
    
    Args:
        location (str): Center location name or address
        category (str): Category of places to find (e.g., restaurants, attractions)
        radius_km (float, optional): Search radius in kilometers (default: 2.0)
        
    Returns:
        str: Nearby places information in natural language
    """
    try:
        print(f"find_nearby_places function called near: {location}, category: {category}, radius: {radius_km}km")
        tool = GeolocationTool()
        nearby_data = tool.find_nearby_places(location, category, float(radius_km))
        description = tool.get_nearby_places_description(nearby_data)
        print(f"Found {nearby_data['count']} nearby places")
        return description
    except Exception as e:
        error_msg = f"Error finding nearby places: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg