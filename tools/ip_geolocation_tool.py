# tools/ip_geolocation_tool.py

import requests
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import re
import socket

class IPGeolocationTool:
    """
    Tool Name: IP Geolocation Tool
    Description: Determines geographic location from IP addresses
    Usage: Can be used to locate users or servers by IP address
    
    System Prompt Addition:
    ```
    You have access to an IP Geolocation Tool that can determine locations from IP addresses.
    When a user asks about tracking IP addresses, finding locations from IPs, or similar requests,
    use the ip_geolocation_tool to get this information.
    
    - To get location from IP: Use ip_geolocation_tool.get_ip_location("8.8.8.8")
    - To get your current IP: Use ip_geolocation_tool.get_current_ip()
    - To check if IP is in a specific region: Use ip_geolocation_tool.check_ip_region("8.8.8.8", "United States")
    
    This tool doesn't require any API keys and returns detailed location data including country,
    city, coordinates, ISP information, and timezone.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "ip_geolocation_tool"
    TOOL_DESCRIPTION = "Determine geographic location from IP addresses"
    TOOL_PARAMETERS = [
        {"name": "ip_address", "type": "string", "description": "IP address to geolocate", "required": True},
        {"name": "region", "type": "string", "description": "Region name for verification checks", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "Where is the IP 8.8.8.8 located?", "tool_call": "ip_geolocation_tool.get_ip_location('8.8.8.8')"},
        {"query": "What is my current IP address?", "tool_call": "ip_geolocation_tool.get_current_ip()"},
        {"query": "Is 104.16.85.20 in the United States?", "tool_call": "ip_geolocation_tool.check_ip_region('104.16.85.20', 'United States')"},
        {"query": "Где находится IP-адрес 77.88.55.88?", "tool_call": "ip_geolocation_tool.get_ip_location('77.88.55.88')"}
    ]
    
    def __init__(self):
        """Initialize the IPGeolocationTool with free IP geolocation API endpoints."""
        # Free IP geolocation API endpoints
        self.ip_api_url = "http://ip-api.com/json/{ip}"  # Primary API
        self.ipify_url = "https://api.ipify.org?format=json"  # For current IP
        self.backup_api_url = "https://ipinfo.io/{ip}/json"  # Backup API
        
        # Headers for API requests
        self.headers = {
            'User-Agent': 'IPGeolocationToolForLLM/1.0'
        }
        
        # Cache for API responses
        self.ip_cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (1 hour)
        self.cache_expiry = 3600
    
    def get_ip_location(self, ip_address: str) -> Dict[str, Any]:
        """
        Get detailed location information for an IP address.
        
        Args:
            ip_address (str): IP address to geolocate
        
        Returns:
            Dict[str, Any]: Detailed information about the IP location
            
        Raises:
            Exception: If the API request fails or IP is invalid
        """
        print(f"Getting location info for IP: {ip_address}")
        
        # Validate IP format
        if not self._is_valid_ip(ip_address):
            raise Exception(f"Invalid IP address format: {ip_address}")
        
        # Check cache
        cache_key = f"ip:{ip_address}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.ip_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached IP data for {ip_address}")
            return self.ip_cache[cache_key]
        
        # Try primary API
        try:
            print(f"Making IP geolocation request for: {ip_address}")
            api_url = self.ip_api_url.format(ip=ip_address)
            response = requests.get(
                api_url, 
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            print(f"Received IP-API response for {ip_address}")
            
            if data.get("status") == "fail":
                raise Exception(f"IP-API lookup failed: {data.get('message', 'Unknown error')}")
            
            # Format the response
            location_data = self._format_ip_api_data(data, ip_address)
            
            # Cache the result
            self.ip_cache[cache_key] = location_data
            self.cache_timestamp[cache_key] = current_time
            
            return location_data
            
        except Exception as e:
            print(f"Primary API failed, trying backup: {str(e)}")
            
            # Try backup API if primary fails
            try:
                backup_api_url = self.backup_api_url.format(ip=ip_address)
                response = requests.get(
                    backup_api_url, 
                    headers=self.headers,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                print(f"Received backup API response for {ip_address}")
                
                # Format the backup API response
                location_data = self._format_ipinfo_data(data, ip_address)
                
                # Cache the result
                self.ip_cache[cache_key] = location_data
                self.cache_timestamp[cache_key] = current_time
                
                return location_data
            
            except Exception as backup_error:
                error_msg = f"IP geolocation failed for {ip_address}: Primary error - {str(e)}, Backup error - {str(backup_error)}"
                print(error_msg)
                raise Exception(error_msg)
    
    def get_current_ip(self) -> Dict[str, Any]:
        """
        Get the current public IP address and its location.
        
        Returns:
            Dict[str, Any]: Current IP address and its location info
            
        Raises:
            Exception: If the API request fails
        """
        print("Getting current IP address")
        
        try:
            # Get current IP
            response = requests.get(self.ipify_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            current_ip = data["ip"]
            print(f"Current IP detected: {current_ip}")
            
            # Get location for this IP
            location_data = self.get_ip_location(current_ip)
            
            # Add current timestamp
            result = {
                "current_ip": current_ip,
                "location": location_data,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error getting current IP: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def check_ip_region(self, ip_address: str, region: str) -> Dict[str, Any]:
        """
        Check if an IP address is located in a specific region (country, city, etc).
        
        Args:
            ip_address (str): IP address to check
            region (str): Region name to compare (country, city, state, etc.)
            
        Returns:
            Dict[str, Any]: Check result with details
            
        Raises:
            Exception: If the API request fails or IP is invalid
        """
        print(f"Checking if IP {ip_address} is in region: {region}")
        
        try:
            # Get IP location
            location_data = self.get_ip_location(ip_address)
            
            # Normalize region name for comparison
            region = region.lower().strip()
            
            # Check various location fields
            location_fields = {
                "country": location_data.get("country", "").lower(),
                "country_code": location_data.get("country_code", "").lower(),
                "region": location_data.get("region", "").lower(),
                "region_name": location_data.get("region_name", "").lower(),
                "city": location_data.get("city", "").lower(),
                "continent": location_data.get("continent", "").lower()
            }
            
            # Check if region matches any field
            is_in_region = False
            matched_field = None
            
            for field, value in location_fields.items():
                if value and (region == value or region in value or value in region):
                    is_in_region = True
                    matched_field = field
                    break
                    
            # Format result
            result = {
                "ip_address": ip_address,
                "query_region": region,
                "is_in_region": is_in_region,
                "ip_location": location_data,
                "matched_field": matched_field,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error checking IP region: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _is_valid_ip(self, ip_address: str) -> bool:
        """
        Validate IPv4 or IPv6 address format.
        
        Args:
            ip_address (str): IP address to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            # Try to parse as IPv4 or IPv6
            socket.inet_pton(socket.AF_INET, ip_address)
            return True
        except socket.error:
            try:
                socket.inet_pton(socket.AF_INET6, ip_address)
                return True
            except socket.error:
                return False
    
    def _format_ip_api_data(self, data: Dict[str, Any], ip_address: str) -> Dict[str, Any]:
        """
        Format the response from IP-API.
        
        Args:
            data (Dict[str, Any]): API response data
            ip_address (str): The queried IP address
            
        Returns:
            Dict[str, Any]: Formatted location data
        """
        return {
            "ip": ip_address,
            "country": data.get("country", ""),
            "country_code": data.get("countryCode", ""),
            "region": data.get("region", ""),
            "region_name": data.get("regionName", ""),
            "city": data.get("city", ""),
            "zip": data.get("zip", ""),
            "latitude": data.get("lat", 0),
            "longitude": data.get("lon", 0),
            "timezone": data.get("timezone", ""),
            "isp": data.get("isp", ""),
            "org": data.get("org", ""),
            "as": data.get("as", ""),
            "as_name": data.get("asname", ""),
            "reverse": data.get("reverse", ""),
            "mobile": data.get("mobile", False),
            "proxy": data.get("proxy", False),
            "hosting": data.get("hosting", False),
            "query_timestamp": datetime.now().isoformat()
        }
    
    def _format_ipinfo_data(self, data: Dict[str, Any], ip_address: str) -> Dict[str, Any]:
        """
        Format the response from IPInfo backup API.
        
        Args:
            data (Dict[str, Any]): API response data
            ip_address (str): The queried IP address
            
        Returns:
            Dict[str, Any]: Formatted location data
        """
        # Parse coordinates if available
        coords = data.get("loc", "").split(",") if "loc" in data else []
        lat = float(coords[0]) if len(coords) > 0 else 0
        lon = float(coords[1]) if len(coords) > 1 else 0
        
        return {
            "ip": ip_address,
            "country": "",  # Not directly provided by IPInfo
            "country_code": data.get("country", ""),
            "region": data.get("region", ""),
            "region_name": data.get("region", ""),
            "city": data.get("city", ""),
            "zip": data.get("postal", ""),
            "latitude": lat,
            "longitude": lon,
            "timezone": data.get("timezone", ""),
            "isp": "",  # Not directly provided
            "org": data.get("org", ""),
            "as": "",  # Not directly provided
            "as_name": data.get("asn", ""),
            "reverse": data.get("hostname", ""),
            "mobile": False,  # Not provided by IPInfo
            "proxy": False,  # Not provided by IPInfo
            "hosting": False,  # Not provided by IPInfo
            "query_timestamp": datetime.now().isoformat()
        }
    
    def get_ip_location_description(self, ip_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of IP location data.
        
        Args:
            ip_data (Dict[str, Any]): IP location data
            
        Returns:
            str: Human-readable IP location description
        """
        ip = ip_data.get("ip", "Unknown IP")
        country = ip_data.get("country", "Unknown Country")
        city = ip_data.get("city", "Unknown City")
        region = ip_data.get("region_name", "")
        
        lat = ip_data.get("latitude", 0)
        lon = ip_data.get("longitude", 0)
        
        isp = ip_data.get("isp", "Unknown ISP")
        org = ip_data.get("org", "")
        asn = ip_data.get("as", "")
        
        timezone = ip_data.get("timezone", "")
        is_proxy = ip_data.get("proxy", False)
        is_hosting = ip_data.get("hosting", False)
        
        # Build the description
        text = f"IP Address: {ip}\n"
        text += f"Location: {city}"
        if region:
            text += f", {region}"
        text += f", {country}\n"
        
        text += f"Coordinates: {lat}, {lon}\n"
        
        if timezone:
            text += f"Timezone: {timezone}\n"
        
        text += f"ISP: {isp}\n"
        
        if org and org != isp:
            text += f"Organization: {org}\n"
        
        if asn:
            text += f"AS Number: {asn}\n"
        
        if is_proxy:
            text += "\nThis IP appears to be a proxy or VPN.\n"
            
        if is_hosting:
            text += "This IP appears to be a hosting provider or data center.\n"
        
        return text

# Functions to expose to the LLM tool system
def get_ip_location(ip_address):
    """
    Get detailed location information for an IP address
    
    Args:
        ip_address (str): IP address to geolocate
        
    Returns:
        str: IP location information in natural language
    """
    try:
        print(f"get_ip_location function called with IP: {ip_address}")
        tool = IPGeolocationTool()
        ip_data = tool.get_ip_location(ip_address)
        description = tool.get_ip_location_description(ip_data)
        print(f"IP location data generated")
        return description
    except Exception as e:
        error_msg = f"Error getting IP location: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_current_ip():
    """
    Get the current public IP address and its location
    
    Returns:
        str: Current IP and its location in natural language
    """
    try:
        print("get_current_ip function called")
        tool = IPGeolocationTool()
        result = tool.get_current_ip()
        current_ip = result["current_ip"]
        description = f"Your current public IP address is: {current_ip}\n\n"
        description += tool.get_ip_location_description(result["location"])
        print(f"Current IP data generated")
        return description
    except Exception as e:
        error_msg = f"Error getting current IP: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def check_ip_region(ip_address, region):
    """
    Check if an IP address is located in a specific region
    
    Args:
        ip_address (str): IP address to check
        region (str): Region name to compare (country, city, state, etc.)
        
    Returns:
        str: Check result with details in natural language
    """
    try:
        print(f"check_ip_region function called with IP: {ip_address}, region: {region}")
        tool = IPGeolocationTool()
        result = tool.check_ip_region(ip_address, region)
        
        ip = result["ip_address"]
        query_region = result["query_region"]
        is_in_region = result["is_in_region"]
        location_data = result["ip_location"]
        
        if is_in_region:
            description = f"Yes, IP address {ip} is located in {query_region}.\n\n"
        else:
            country = location_data.get("country", "unknown country")
            city = location_data.get("city", "unknown city")
            description = f"No, IP address {ip} is not located in {query_region}. "
            description += f"It is located in {city}, {country}.\n\n"
        
        description += tool.get_ip_location_description(location_data)
        
        print(f"IP region check completed")
        return description
    except Exception as e:
        error_msg = f"Error checking IP region: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg