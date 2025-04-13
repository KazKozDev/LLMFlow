# tools/time_tool.py

import datetime
import pytz
import re
from typing import Dict, List, Any, Optional, Union, Tuple
from dateutil import parser
from dateutil.relativedelta import relativedelta
import calendar

class TimeTool:
    """
    Tool Name: Time Information Tool
    Description: Provides time-related information for different timezones
    Usage: Can be used to get current time, convert between timezones, and calculate time differences
    
    System Prompt Addition:
    ```
    You have access to a Time Tool that can provide information about time in different locations.
    When a user asks about current time, timezone conversions, or time differences, use the time_tool to get this information.
    
    - To get current time: Use time_tool.get_current_time("New York") or time_tool.get_current_time("Tokyo")
    - To convert time: Use time_tool.convert_time("2023-04-15 14:30", "London", "Sydney")
    - To calculate time difference: Use time_tool.get_time_difference("Paris", "Los Angeles")
    - To list timezones: Use time_tool.list_timezones("Asia") or time_tool.list_timezones()
    
    This tool doesn't require any API keys and provides accurate time information for any location worldwide.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "time_tool"
    TOOL_DESCRIPTION = "Get time-related information for different locations and timezones"
    TOOL_PARAMETERS = [
        {"name": "location", "type": "string", "description": "City name or timezone identifier", "required": True},
        {"name": "target_location", "type": "string", "description": "Target location for conversion or comparison", "required": False},
        {"name": "time_string", "type": "string", "description": "Time string for conversion (default: current time)", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What time is it in Tokyo?", "tool_call": "time_tool.get_current_time('Tokyo')"},
        {"query": "Convert 3pm New York time to London", "tool_call": "time_tool.convert_time('3pm', 'New York', 'London')"},
        {"query": "What's the time difference between Dubai and Singapore?", "tool_call": "time_tool.get_time_difference('Dubai', 'Singapore')"},
        {"query": "Сколько времени сейчас в Москве?", "tool_call": "time_tool.get_current_time('Moscow')"}
    ]
    
    def __init__(self):
        """Initialize the TimeTool with timezone mappings."""
        # Popular city to timezone mappings
        self.city_to_timezone = {
            # North America
            "new york": "America/New_York",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "toronto": "America/Toronto",
            "vancouver": "America/Vancouver",
            "mexico city": "America/Mexico_City",
            "havana": "America/Havana",
            "denver": "America/Denver",
            "phoenix": "America/Phoenix",
            "anchorage": "America/Anchorage",
            "honolulu": "Pacific/Honolulu",
            
            # South America
            "sao paulo": "America/Sao_Paulo",
            "buenos aires": "America/Argentina/Buenos_Aires",
            "rio de janeiro": "America/Sao_Paulo",
            "bogota": "America/Bogota",
            "lima": "America/Lima",
            "santiago": "America/Santiago",
            
            # Europe
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "berlin": "Europe/Berlin",
            "rome": "Europe/Rome",
            "madrid": "Europe/Madrid",
            "amsterdam": "Europe/Amsterdam",
            "brussels": "Europe/Brussels",
            "zurich": "Europe/Zurich",
            "stockholm": "Europe/Stockholm",
            "oslo": "Europe/Oslo",
            "copenhagen": "Europe/Copenhagen",
            "helsinki": "Europe/Helsinki",
            "vienna": "Europe/Vienna",
            "athens": "Europe/Athens",
            "moscow": "Europe/Moscow",
            "dublin": "Europe/Dublin",
            "warsaw": "Europe/Warsaw",
            "budapest": "Europe/Budapest",
            "prague": "Europe/Prague",
            "istanbul": "Europe/Istanbul",
            "kiev": "Europe/Kiev",
            "kyiv": "Europe/Kiev",
            
            # Asia
            "tokyo": "Asia/Tokyo",
            "beijing": "Asia/Shanghai",
            "shanghai": "Asia/Shanghai",
            "hong kong": "Asia/Hong_Kong",
            "singapore": "Asia/Singapore",
            "seoul": "Asia/Seoul",
            "bangkok": "Asia/Bangkok",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "kolkata": "Asia/Kolkata",
            "karachi": "Asia/Karachi",
            "dubai": "Asia/Dubai",
            "manila": "Asia/Manila",
            "jakarta": "Asia/Jakarta",
            "kuala lumpur": "Asia/Kuala_Lumpur",
            "taipei": "Asia/Taipei",
            "ho chi minh city": "Asia/Ho_Chi_Minh",
            "yangon": "Asia/Yangon",
            "dhaka": "Asia/Dhaka",
            "riyadh": "Asia/Riyadh",
            "tehran": "Asia/Tehran",
            "Baghdad": "Asia/Baghdad",
            
            # Africa
            "cairo": "Africa/Cairo",
            "johannesburg": "Africa/Johannesburg",
            "nairobi": "Africa/Nairobi",
            "lagos": "Africa/Lagos",
            "casablanca": "Africa/Casablanca",
            "tunis": "Africa/Tunis",
            "algiers": "Africa/Algiers",
            "khartoum": "Africa/Khartoum",
            "accra": "Africa/Accra",
            "addis ababa": "Africa/Addis_Ababa",
            
            # Oceania
            "sydney": "Australia/Sydney",
            "melbourne": "Australia/Melbourne",
            "perth": "Australia/Perth",
            "brisbane": "Australia/Brisbane",
            "auckland": "Pacific/Auckland",
            "wellington": "Pacific/Auckland",
            "fiji": "Pacific/Fiji",
            "adelaide": "Australia/Adelaide",
            "hobart": "Australia/Hobart",
            
            # Russian cities
            "saint petersburg": "Europe/Moscow",
            "санкт-петербург": "Europe/Moscow",
            "москва": "Europe/Moscow",
            "novosibirsk": "Asia/Novosibirsk",
            "новосибирск": "Asia/Novosibirsk",
            "yekaterinburg": "Asia/Yekaterinburg",
            "екатеринбург": "Asia/Yekaterinburg",
            "vladivostok": "Asia/Vladivostok",
            "владивосток": "Asia/Vladivostok",
            "irkutsk": "Asia/Irkutsk",
            "иркутск": "Asia/Irkutsk",
            
            # Common UTC offsets
            "utc": "UTC",
            "gmt": "UTC",
            "est": "America/New_York",
            "edt": "America/New_York",
            "cst": "America/Chicago",
            "cdt": "America/Chicago",
            "mst": "America/Denver",
            "mdt": "America/Denver",
            "pst": "America/Los_Angeles",
            "pdt": "America/Los_Angeles",
            "bst": "Europe/London",
            "cet": "Europe/Paris",
            "cest": "Europe/Paris",
            "jst": "Asia/Tokyo",
            "ist": "Asia/Kolkata",
            "aest": "Australia/Sydney",
            "aedt": "Australia/Sydney",
            "awst": "Australia/Perth",
            "nzst": "Pacific/Auckland",
            "nzdt": "Pacific/Auckland"
        }
        
        # Use pytz for timezone data
        self.all_timezones = pytz.all_timezones
        
        # Cache for timezone objects
        self.timezone_cache = {}
        
        # Regex patterns for time parsing
        self.time_patterns = [
            # 3pm, 3 pm, 3 PM
            r"(\d+)(?:\s*)?([ap]\.?m\.?)",
            # 15:30, 15.30, 15h30
            r"(\d{1,2})(?::|\.|h)(\d{2})",
            # 3:30pm, 3.30 pm, 3h30 PM
            r"(\d{1,2})(?::|\.|h)(\d{2})(?:\s*)?([ap]\.?m\.?)?",
        ]
        
        # Mapping of countries and continents to common timezones
        self.region_timezones = {
            "north america": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Toronto", "America/Vancouver", "America/Mexico_City"],
            "south america": ["America/Sao_Paulo", "America/Argentina/Buenos_Aires", "America/Bogota", "America/Lima", "America/Santiago"],
            "europe": ["Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow", "Europe/Istanbul"],
            "asia": ["Asia/Tokyo", "Asia/Shanghai", "Asia/Singapore", "Asia/Dubai", "Asia/Kolkata", "Asia/Seoul", "Asia/Bangkok"],
            "africa": ["Africa/Cairo", "Africa/Johannesburg", "Africa/Lagos", "Africa/Nairobi", "Africa/Casablanca"],
            "oceania": ["Australia/Sydney", "Australia/Perth", "Pacific/Auckland", "Pacific/Fiji"],
            "australia": ["Australia/Sydney", "Australia/Melbourne", "Australia/Brisbane", "Australia/Perth", "Australia/Adelaide"],
            "usa": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu"],
            "canada": ["America/Toronto", "America/Vancouver", "America/Edmonton", "America/Winnipeg", "America/Halifax", "America/St_Johns"],
            "united states": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles", "America/Anchorage", "Pacific/Honolulu"],
            "united kingdom": ["Europe/London"],
            "uk": ["Europe/London"],
            "russia": ["Europe/Moscow", "Europe/Kaliningrad", "Asia/Yekaterinburg", "Asia/Novosibirsk", "Asia/Irkutsk", "Asia/Vladivostok"],
            "china": ["Asia/Shanghai"],
            "japan": ["Asia/Tokyo"],
            "india": ["Asia/Kolkata"],
            "germany": ["Europe/Berlin"],
            "france": ["Europe/Paris"],
            "italy": ["Europe/Rome"],
            "spain": ["Europe/Madrid"],
            "brazil": ["America/Sao_Paulo", "America/Manaus", "America/Recife"],
            "mexico": ["America/Mexico_City", "America/Tijuana", "America/Cancun"],
        }
    
    def get_current_time(self, location: str) -> Dict[str, Any]:
        """
        Get the current time for a specified location.
        
        Args:
            location (str): City name, country, or timezone identifier
        
        Returns:
            Dict[str, Any]: Current time data
            
        Raises:
            Exception: If the location cannot be resolved to a timezone
        """
        print(f"Getting current time for location: {location}")
        
        # Get the timezone for the location
        timezone = self._get_timezone(location)
        
        if not timezone:
            raise Exception(f"Could not determine timezone for location: {location}")
        
        # Get current time in that timezone
        utc_now = datetime.datetime.now(pytz.UTC)
        local_time = utc_now.astimezone(timezone)
        
        # Format the response
        result = {
            "query": location,
            "timezone": {
                "name": str(timezone),
                "abbreviation": self._get_timezone_abbreviation(timezone, local_time),
                "offset": self._get_timezone_offset(timezone, local_time),
                "offset_hours": self._get_offset_hours(timezone, local_time)
            },
            "datetime": {
                "iso": local_time.isoformat(),
                "year": local_time.year,
                "month": local_time.month,
                "month_name": local_time.strftime("%B"),
                "day": local_time.day,
                "weekday": local_time.strftime("%A"),
                "hour": local_time.hour,
                "hour_12": int(local_time.strftime("%I")),
                "minute": local_time.minute,
                "second": local_time.second,
                "am_pm": local_time.strftime("%p"),
                "timestamp": int(local_time.timestamp())
            },
            "formatted": {
                "date_full": local_time.strftime("%A, %B %d, %Y"),
                "date_short": local_time.strftime("%Y-%m-%d"),
                "time_24h": local_time.strftime("%H:%M:%S"),
                "time_12h": local_time.strftime("%I:%M:%S %p"),
                "datetime": local_time.strftime("%Y-%m-%d %H:%M:%S"),
                "datetime_full": local_time.strftime("%A, %B %d, %Y %I:%M:%S %p")
            },
            "additional_info": {
                "dst_active": self._is_dst(timezone, local_time),
                "day_of_year": int(local_time.strftime("%j")),
                "week_of_year": int(local_time.strftime("%U")),
                "days_in_month": calendar.monthrange(local_time.year, local_time.month)[1]
            }
        }
        
        return result
    
    def convert_time(self, time_string: str, source_location: str, target_location: str) -> Dict[str, Any]:
        """
        Convert a time from one location to another.
        
        Args:
            time_string (str): Time to convert (e.g., "2023-04-15 14:30", "3pm", "15:45")
            source_location (str): Source location or timezone
            target_location (str): Target location or timezone
        
        Returns:
            Dict[str, Any]: Converted time data
            
        Raises:
            Exception: If the locations cannot be resolved to timezones or time string is invalid
        """
        print(f"Converting time: {time_string} from {source_location} to {target_location}")
        
        # Get timezones for both locations
        source_tz = self._get_timezone(source_location)
        target_tz = self._get_timezone(target_location)
        
        if not source_tz:
            raise Exception(f"Could not determine timezone for source location: {source_location}")
        if not target_tz:
            raise Exception(f"Could not determine timezone for target location: {target_location}")
        
        # Parse the time string
        dt = self._parse_time_string(time_string, source_tz)
        if not dt:
            raise Exception(f"Could not parse time string: {time_string}")
        
        # Convert the time to the target timezone
        converted_time = dt.astimezone(target_tz)
        
        # Calculate time difference
        time_diff = self._get_offset_hours(target_tz, converted_time) - self._get_offset_hours(source_tz, dt)
        
        # Format the response
        result = {
            "source": {
                "location": source_location,
                "time": dt.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": str(source_tz),
                "offset_hours": self._get_offset_hours(source_tz, dt)
            },
            "target": {
                "location": target_location,
                "time": converted_time.strftime("%Y-%m-%d %H:%M:%S"),
                "timezone": str(target_tz),
                "offset_hours": self._get_offset_hours(target_tz, converted_time)
            },
            "time_difference": {
                "hours": time_diff,
                "formatted": f"{abs(time_diff):+.1f} hours" if time_diff else "Same time"
            },
            "formatted": {
                "source_time_12h": dt.strftime("%I:%M:%S %p"),
                "target_time_12h": converted_time.strftime("%I:%M:%S %p"),
                "source_time_24h": dt.strftime("%H:%M:%S"),
                "target_time_24h": converted_time.strftime("%H:%M:%S"),
                "source_datetime": dt.strftime("%Y-%m-%d %I:%M:%S %p"),
                "target_datetime": converted_time.strftime("%Y-%m-%d %I:%M:%S %p")
            },
            "same_day": dt.date() == converted_time.date(),
            "day_difference": (converted_time.date() - dt.date()).days
        }
        
        return result
    
    def get_time_difference(self, location1: str, location2: str) -> Dict[str, Any]:
        """
        Calculate the time difference between two locations.
        
        Args:
            location1 (str): First location or timezone
            location2 (str): Second location or timezone
        
        Returns:
            Dict[str, Any]: Time difference data
            
        Raises:
            Exception: If the locations cannot be resolved to timezones
        """
        print(f"Calculating time difference between {location1} and {location2}")
        
        # Get timezones for both locations
        tz1 = self._get_timezone(location1)
        tz2 = self._get_timezone(location2)
        
        if not tz1:
            raise Exception(f"Could not determine timezone for location: {location1}")
        if not tz2:
            raise Exception(f"Could not determine timezone for location: {location2}")
        
        # Get current time in both timezones
        utc_now = datetime.datetime.now(pytz.UTC)
        time1 = utc_now.astimezone(tz1)
        time2 = utc_now.astimezone(tz2)
        
        # Calculate the difference in hours
        offset1 = self._get_offset_hours(tz1, time1)
        offset2 = self._get_offset_hours(tz2, time2)
        hour_diff = offset2 - offset1
        
        # Calculate time difference
        time_diff = abs(hour_diff)
        time_diff_hours = int(time_diff)
        time_diff_minutes = int((time_diff - time_diff_hours) * 60)
        
        # Determine the direction of the difference
        direction = "ahead of" if hour_diff > 0 else "behind" if hour_diff < 0 else "same as"
        
        # Format the response
        result = {
            "locations": {
                "location1": {
                    "name": location1,
                    "timezone": str(tz1),
                    "current_time": time1.strftime("%Y-%m-%d %H:%M:%S"),
                    "offset_hours": offset1
                },
                "location2": {
                    "name": location2,
                    "timezone": str(tz2),
                    "current_time": time2.strftime("%Y-%m-%d %H:%M:%S"),
                    "offset_hours": offset2
                }
            },
            "difference": {
                "hours": hour_diff,
                "absolute_hours": time_diff,
                "hours_minutes": f"{time_diff_hours}h {time_diff_minutes}m",
                "direction": direction,
                "description": f"{location2} is {time_diff_hours}h {time_diff_minutes}m {direction} {location1}" if hour_diff != 0 else f"{location2} is in the same timezone as {location1}"
            },
            "working_hours": {
                "overlapping": self._calculate_working_hours_overlap(offset1, offset2),
                "notes": self._get_working_hours_notes(hour_diff)
            },
            "best_meeting_times": self._suggest_meeting_times(offset1, offset2)
        }
        
        return result
    
    def list_timezones(self, region: str = None) -> Dict[str, Any]:
        """
        List available timezones, optionally filtered by region.
        
        Args:
            region (str, optional): Region to filter timezones (continent, country, etc.)
        
        Returns:
            Dict[str, Any]: List of timezones
        """
        print(f"Listing timezones for region: {region or 'all'}")
        
        # If a region is specified, try to filter the timezones
        filtered_zones = []
        if region:
            region_lower = region.lower()
            
            # Check if it's a predefined region
            if region_lower in self.region_timezones:
                filtered_zones = self.region_timezones[region_lower]
            else:
                # Otherwise, filter by string matching
                filtered_zones = [tz for tz in self.all_timezones if region_lower in tz.lower()]
        else:
            # No region specified, include a reasonable subset of timezones
            for region_zones in self.region_timezones.values():
                for zone in region_zones:
                    if zone not in filtered_zones:
                        filtered_zones.append(zone)
        
        # Get current time for each timezone
        utc_now = datetime.datetime.now(pytz.UTC)
        timezone_data = []
        
        for tz_name in filtered_zones:
            try:
                tz = pytz.timezone(tz_name)
                local_time = utc_now.astimezone(tz)
                
                timezone_data.append({
                    "name": tz_name,
                    "abbreviation": self._get_timezone_abbreviation(tz, local_time),
                    "offset": self._get_timezone_offset(tz, local_time),
                    "offset_hours": self._get_offset_hours(tz, local_time),
                    "current_time": local_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "dst_active": self._is_dst(tz, local_time)
                })
            except Exception as e:
                print(f"Error processing timezone {tz_name}: {e}")
                continue
        
        # Sort by offset
        timezone_data.sort(key=lambda x: x["offset_hours"])
        
        # Format the response
        result = {
            "region": region or "global selection",
            "count": len(timezone_data),
            "timezones": timezone_data,
            "reference_time": utc_now.strftime("%Y-%m-%d %H:%M:%S UTC")
        }
        
        return result
    
    def _get_timezone(self, location: str) -> Optional[pytz.timezone]:
        """
        Get a timezone object from a location string.
        
        Args:
            location (str): Location string (city, country, timezone, etc.)
            
        Returns:
            Optional[pytz.timezone]: Timezone object or None if not found
        """
        if not location:
            return None
            
        # Check cache first
        if location in self.timezone_cache:
            return self.timezone_cache[location]
        
        # Normalize the location string
        location_lower = location.lower()
        
        # Direct mapping if available
        if location_lower in self.city_to_timezone:
            timezone_str = self.city_to_timezone[location_lower]
            try:
                timezone = pytz.timezone(timezone_str)
                self.timezone_cache[location] = timezone
                return timezone
            except pytz.exceptions.UnknownTimeZoneError:
                pass
        
        # Check if it's a valid timezone name
        try:
            if location in pytz.all_timezones:
                timezone = pytz.timezone(location)
                self.timezone_cache[location] = timezone
                return timezone
        except pytz.exceptions.UnknownTimeZoneError:
            pass
        
        # Try to match with timezone names
        for tz_name in pytz.all_timezones:
            if location_lower in tz_name.lower():
                try:
                    timezone = pytz.timezone(tz_name)
                    self.timezone_cache[location] = timezone
                    return timezone
                except pytz.exceptions.UnknownTimeZoneError:
                    pass
        
        # Try to extract a timezone from common patterns
        timezone_match = re.search(r'(GMT|UTC)([+-]\d{1,2})(?::(\d{2}))?', location, re.IGNORECASE)
        if timezone_match:
            hours = int(timezone_match.group(2))
            minutes = int(timezone_match.group(3) or 0)
            sign = -1 if hours < 0 else 1
            
            # Create a fixed offset timezone
            offset = datetime.timedelta(hours=abs(hours), minutes=minutes)
            if sign < 0:
                offset = -offset
                
            timezone = datetime.timezone(offset, name=f"UTC{hours:+d}:{minutes:02d}")
            self.timezone_cache[location] = timezone
            return timezone
        
        # Last resort: try to find partial matches in city names
        best_match = None
        for city, tz_str in self.city_to_timezone.items():
            if city in location_lower or location_lower in city:
                best_match = tz_str
                break
                
        if best_match:
            try:
                timezone = pytz.timezone(best_match)
                self.timezone_cache[location] = timezone
                return timezone
            except pytz.exceptions.UnknownTimeZoneError:
                pass
        
        return None
    
    def _parse_time_string(self, time_str: str, timezone: pytz.timezone) -> Optional[datetime.datetime]:
        """
        Parse a time string into a datetime object.
        
        Args:
            time_str (str): Time string to parse
            timezone (pytz.timezone): Timezone to use
            
        Returns:
            Optional[datetime.datetime]: Datetime object or None if parsing fails
        """
        if not time_str:
            # If no time string is provided, use current time
            return datetime.datetime.now(timezone)
        
        # Try to parse as ISO format
        try:
            dt = parser.parse(time_str)
            # If no timezone info, assume the provided timezone
            if dt.tzinfo is None:
                dt = timezone.localize(dt)
            return dt
        except (ValueError, parser.ParserError):
            pass
        
        # Try common time formats using regex
        # First, check if the time includes just a time (no date)
        for pattern in self.time_patterns:
            match = re.match(pattern, time_str)
            if match:
                groups = match.groups()
                if len(groups) == 2:  # Simple hour + am/pm
                    hour = int(groups[0])
                    am_pm = groups[1].lower()
                    
                    # Adjust for 12-hour format
                    if 'p' in am_pm and hour < 12:
                        hour += 12
                    elif 'a' in am_pm and hour == 12:
                        hour = 0
                        
                    # Create datetime with current date
                    now = datetime.datetime.now(timezone)
                    dt = timezone.localize(datetime.datetime(
                        now.year, now.month, now.day, hour, 0, 0
                    ))
                    return dt
                    
                elif len(groups) >= 2:  # Hour + minute
                    hour = int(groups[0])
                    minute = int(groups[1])
                    
                    # Check if there's an AM/PM indicator in the third group
                    if len(groups) > 2 and groups[2]:
                        am_pm = groups[2].lower()
                        if 'p' in am_pm and hour < 12:
                            hour += 12
                        elif 'a' in am_pm and hour == 12:
                            hour = 0
                    
                    # Create datetime with current date
                    now = datetime.datetime.now(timezone)
                    dt = timezone.localize(datetime.datetime(
                        now.year, now.month, now.day, hour, minute, 0
                    ))
                    return dt
        
        # Try very flexible parsing as a last resort
        try:
            # If it's just a number, assume it's an hour today
            if time_str.isdigit():
                hour = int(time_str)
                if 0 <= hour < 24:
                    now = datetime.datetime.now(timezone)
                    dt = timezone.localize(datetime.datetime(
                        now.year, now.month, now.day, hour, 0, 0
                    ))
                    return dt
            
            # Special words
            if time_str.lower() in ["now", "current time", "current"]:
                return datetime.datetime.now(timezone)
            
            if time_str.lower() in ["today", "day"]:
                now = datetime.datetime.now(timezone)
                return timezone.localize(datetime.datetime(now.year, now.month, now.day, 12, 0, 0))
            
            if time_str.lower() in ["tomorrow"]:
                now = datetime.datetime.now(timezone)
                tomorrow = now + datetime.timedelta(days=1)
                return timezone.localize(datetime.datetime(tomorrow.year, tomorrow.month, tomorrow.day, 12, 0, 0))
            
            if time_str.lower() in ["yesterday"]:
                now = datetime.datetime.now(timezone)
                yesterday = now - datetime.timedelta(days=1)
                return timezone.localize(datetime.datetime(yesterday.year, yesterday.month, yesterday.day, 12, 0, 0))
            
            # Last attempt with dateutil parser
            dt = parser.parse(time_str, fuzzy=True)
            if dt.tzinfo is None:
                dt = timezone.localize(dt)
            return dt
            
        except Exception as e:
            print(f"All time parsing methods failed for '{time_str}': {e}")
            return None
    
    def _get_timezone_offset(self, timezone: pytz.timezone, dt: datetime.datetime) -> str:
        """
        Get the offset string of a timezone.
        
        Args:
            timezone (pytz.timezone): Timezone
            dt (datetime.datetime): Datetime to calculate offset for
            
        Returns:
            str: Timezone offset string (e.g., +09:00)
        """
        offset = dt.strftime("%z")
        if offset:
            # Format as +HH:MM
            return f"{offset[:3]}:{offset[3:]}"
        return "Unknown"
    
    def _get_offset_hours(self, timezone: pytz.timezone, dt: datetime.datetime) -> float:
        """
        Get the offset in decimal hours.
        
        Args:
            timezone (pytz.timezone): Timezone
            dt (datetime.datetime): Datetime to calculate offset for
            
        Returns:
            float: Offset in hours
        """
        offset_str = dt.strftime("%z")
        if offset_str:
            hours = int(offset_str[:3])
            minutes = int(offset_str[3:]) if len(offset_str) > 3 else 0
            
            # Convert to decimal hours
            offset_hours = hours + (minutes / 60)
            return offset_hours
            
        return 0.0
    
    def _get_timezone_abbreviation(self, timezone: pytz.timezone, dt: datetime.datetime) -> str:
        """
        Get the abbreviation for a timezone at a specific datetime.
        
        Args:
            timezone (pytz.timezone): Timezone
            dt (datetime.datetime): Datetime to get abbreviation for
            
        Returns:
            str: Timezone abbreviation (e.g., EDT, JST)
        """
        # Try to get the abbreviation from tzname
        try:
            tzname = dt.strftime("%Z")
            if tzname and tzname != "+00" and tzname != "UTC":
                return tzname
        except:
            pass
        
        # Common timezone abbreviations
        common_abbrevs = {
            "America/New_York": ["EST", "EDT"],
            "America/Chicago": ["CST", "CDT"],
            "America/Denver": ["MST", "MDT"],
            "America/Los_Angeles": ["PST", "PDT"],
            "Europe/London": ["GMT", "BST"],
            "Europe/Paris": ["CET", "CEST"],
            "Europe/Moscow": ["MSK"],
            "Asia/Tokyo": ["JST"],
            "Asia/Shanghai": ["CST"],
            "Asia/Kolkata": ["IST"],
            "Australia/Sydney": ["AEST", "AEDT"],
            "Pacific/Auckland": ["NZST", "NZDT"]
        }
        
        tz_name = str(timezone)
        if tz_name in common_abbrevs:
            abbrevs = common_abbrevs[tz_name]
            # Use DST or standard time abbreviation
            is_dst = self._is_dst(timezone, dt)
            return abbrevs[1] if is_dst and len(abbrevs) > 1 else abbrevs[0]
        
        # Fallback to offset format (UTC+9)
        offset = self._get_offset_hours(timezone, dt)
        sign = "+" if offset >= 0 else "-"
        return f"UTC{sign}{abs(int(offset)):d}"
    
    def _is_dst(self, timezone: pytz.timezone, dt: datetime.datetime) -> bool:
        """
        Check if a timezone is in DST at a specific datetime.
        
        Args:
            timezone (pytz.timezone): Timezone
            dt (datetime.datetime): Datetime to check
            
        Returns:
            bool: True if DST is active, False otherwise
        """
        try:
            # Check if the timezone has DST
            return dt.dst() != datetime.timedelta(0)
        except:
            return False
    
    def _calculate_working_hours_overlap(self, offset1: float, offset2: float) -> Dict[str, Any]:
        """
        Calculate the overlap in standard working hours between two timezones.
        
        Args:
            offset1 (float): UTC offset for the first location in hours
            offset2 (float): UTC offset for the second location in hours
            
        Returns:
            Dict[str, Any]: Overlap details including hours, quality, and time range
        """
        # Calculate the difference in hours
        diff_hours = offset2 - offset1
        
        # Standard working hours: 9am to 5pm (8 hours)
        # Calculate the working hours in each timezone relative to each other
        if abs(diff_hours) >= 24:
            # Handle edge case where difference is more than 24 hours
            diff_hours = diff_hours % 24
        
        # Calculate the overlap of 9am-5pm
        if abs(diff_hours) >= 16:  # No overlap if difference is more than 16 hours
            overlap_hours = 0
            start_hour = None
            end_hour = None
        else:
            # Location 1 working hours: 9am-5pm
            # Location 2 working hours shifted by difference: (9+diff)-(17+diff)
            loc1_start, loc1_end = 9, 17
            loc2_start = (9 + diff_hours) % 24
            loc2_end = (17 + diff_hours) % 24
            
            # Handle day boundary crossing
            if loc2_start > loc2_end:
                # Working hours span midnight
                if loc1_start <= loc2_end:
                    # Overlap in the early hours
                    overlap_start = loc1_start
                    overlap_end = loc2_end
                    overlap_hours = overlap_end - overlap_start
                    start_hour = overlap_start
                    end_hour = overlap_end
                elif loc1_end >= loc2_start:
                    # Overlap in the late hours
                    overlap_start = loc2_start
                    overlap_end = loc1_end
                    overlap_hours = overlap_end - overlap_start
                    start_hour = overlap_start
                    end_hour = overlap_end
                else:
                    # No overlap
                    overlap_hours = 0
                    start_hour = None
                    end_hour = None
            else:
                # Normal case
                overlap_start = max(loc1_start, loc2_start)
                overlap_end = min(loc1_end, loc2_end)
                
                if overlap_start < overlap_end:
                    overlap_hours = overlap_end - overlap_start
                    start_hour = overlap_start
                    end_hour = overlap_end
                else:
                    overlap_hours = 0
                    start_hour = None
                    end_hour = None
        
        # Format the response
        result = {
            "hours": overlap_hours,
            "has_overlap": overlap_hours > 0,
            "quality": "No overlap"  # Default value
        }
        
        if overlap_hours > 0:
            # Format the overlap time
            start_format = f"{int(start_hour)}:{(start_hour % 1) * 60:02.0f}"
            end_format = f"{int(end_hour)}:{(end_hour % 1) * 60:02.0f}"
            
            result["overlap_time"] = f"{start_format}-{end_format}"
            
            # Set quality based on overlap hours
            if overlap_hours >= 6:
                result["quality"] = "Excellent"
            elif overlap_hours >= 4:
                result["quality"] = "Good"
            elif overlap_hours >= 2:
                result["quality"] = "Fair"
            else:
                result["quality"] = "Limited"
        else:
            result["overlap_time"] = "None"
        
        return result
    
    def _get_working_hours_notes(self, hour_diff: float) -> str:
        """
        Get notes about working hours based on time difference.
        
        Args:
            hour_diff (float): Hour difference between locations
            
        Returns:
            str: Notes about working hours
        """
        abs_diff = abs(hour_diff)
        
        if abs_diff < 3:
            return "Minimal difference, easy to schedule meetings during standard working hours."
        elif abs_diff < 6:
            return "Moderate difference, consider scheduling meetings in the morning for one location and afternoon for the other."
        elif abs_diff < 9:
            return "Significant difference, schedule meetings at the beginning or end of the workday to accommodate both locations."
        elif abs_diff < 12:
            return "Major difference, one location will need to have meetings outside standard hours. Consider alternating who accommodates."
        else:
            return "Extreme difference, very limited or no overlap in standard working hours. Video recordings and asynchronous communication recommended."
    
    def _suggest_meeting_times(self, offset1: float, offset2: float) -> List[Dict[str, str]]:
        """
        Suggest good meeting times for two timezones.
        
        Args:
            offset1 (float): Offset in hours for location 1
            offset2 (float): Offset in hours for location 2
            
        Returns:
            List[Dict[str, str]]: List of suggested meeting times
        """
        # Calculate the difference in hours
        diff_hours = offset2 - offset1
        abs_diff = abs(diff_hours)
        
        # Initialize suggestions
        suggestions = []
        
        if abs_diff < 6:
            # Small difference, suggest mid-day meetings
            suggestions.append({
                "location1_time": "13:00",
                "location2_time": f"{(13 + diff_hours) % 24:02.0f}:00",
                "quality": "Optimal"
            })
            suggestions.append({
                "location1_time": "15:00",
                "location2_time": f"{(15 + diff_hours) % 24:02.0f}:00",
                "quality": "Good"
            })
            
        elif abs_diff < 10:
            # Medium difference, suggest early/late meetings
            suggestions.append({
                "location1_time": "08:00",
                "location2_time": f"{(8 + diff_hours) % 24:02.0f}:00",
                "quality": "Good for location 1 morning"
            })
            suggestions.append({
                "location1_time": "16:00",
                "location2_time": f"{(16 + diff_hours) % 24:02.0f}:00",
                "quality": "Good for location 1 afternoon"
            })
            
        else:
            # Large difference, suggest compromise times
            suggestions.append({
                "location1_time": "07:00",
                "location2_time": f"{(7 + diff_hours) % 24:02.0f}:00",
                "quality": "Early for location 1"
            })
            suggestions.append({
                "location1_time": "19:00",
                "location2_time": f"{(19 + diff_hours) % 24:02.0f}:00",
                "quality": "Late for location 1"
            })
        
        # Check for very difficult cases
        if abs_diff > 14:
            suggestions.append({
                "location1_time": "22:00",
                "location2_time": f"{(22 + diff_hours) % 24:02.0f}:00",
                "quality": "Difficult (outside working hours)"
            })
        
        return suggestions
    
    def get_time_description(self, time_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of current time.
        
        Args:
            time_data (Dict[str, Any]): Time data from get_current_time
            
        Returns:
            str: Human-readable time description
        """
        location = time_data["query"]
        timezone_name = time_data["timezone"]["name"]
        timezone_abbr = time_data["timezone"]["abbreviation"]
        offset = time_data["timezone"]["offset"]
        
        date_full = time_data["formatted"]["date_full"]
        time_12h = time_data["formatted"]["time_12h"]
        
        dst_status = "is currently observing Daylight Saving Time" if time_data["additional_info"]["dst_active"] else "is not currently observing Daylight Saving Time"
        
        description = f"Current time in {location} ({timezone_abbr}) is {time_12h} on {date_full}.\n"
        description += f"This location is in the {timezone_name} timezone with UTC offset {offset}.\n"
        description += f"The timezone {dst_status}."
        
        return description
    
    def get_time_conversion_description(self, conversion_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of time conversion.
        
        Args:
            conversion_data (Dict[str, Any]): Conversion data from convert_time
            
        Returns:
            str: Human-readable conversion description
        """
        source_location = conversion_data["source"]["location"]
        source_time = conversion_data["formatted"]["source_time_12h"]
        source_timezone = conversion_data["source"]["timezone"]
        
        target_location = conversion_data["target"]["location"]
        target_time = conversion_data["formatted"]["target_time_12h"]
        target_timezone = conversion_data["target"]["timezone"]
        
        time_diff = conversion_data["time_difference"]["formatted"]
        same_day = conversion_data["same_day"]
        day_diff = conversion_data["day_difference"]
        
        description = f"When it's {source_time} in {source_location} ({source_timezone}), "
        description += f"it's {target_time} in {target_location} ({target_timezone}).\n"
        
        description += f"Time difference: {time_diff}.\n"
        
        if not same_day:
            day_word = "day" if abs(day_diff) == 1 else "days"
            ahead_behind = "ahead" if day_diff > 0 else "behind"
            description += f"{target_location} is {abs(day_diff)} {day_word} {ahead_behind} {source_location}."
        
        return description
    
    def get_time_difference_description(self, difference_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of time difference.
        
        Args:
            difference_data (Dict[str, Any]): Difference data from get_time_difference
            
        Returns:
            str: Human-readable difference description
        """
        # Extract location names safely
        location1 = difference_data.get("locations", {}).get("location1", {}).get("name", "Location 1")
        location2 = difference_data.get("locations", {}).get("location2", {}).get("name", "Location 2")
        
        # Extract times and timezones safely
        time1 = difference_data.get("locations", {}).get("location1", {}).get("current_time", "Unknown time")
        time2 = difference_data.get("locations", {}).get("location2", {}).get("current_time", "Unknown time")
        
        timezone1 = difference_data.get("locations", {}).get("location1", {}).get("timezone", "Unknown timezone")
        timezone2 = difference_data.get("locations", {}).get("location2", {}).get("timezone", "Unknown timezone")
        
        # Extract difference description safely
        difference_desc = difference_data.get("difference", {}).get("description", f"Time difference between {location1} and {location2} could not be determined")
        
        # Extract working hours info safely
        working_hours = difference_data.get("working_hours", {})
        
        # Format the description
        description = f"Current time comparison:\n"
        description += f"- {location1} ({timezone1}): {time1}\n"
        description += f"- {location2} ({timezone2}): {time2}\n\n"
        
        description += f"Time difference: {difference_desc}\n\n"
        
        # Get working hours quality, with fallback
        quality = working_hours.get("quality", "Unknown")
        
        # Safe checks for all working hours fields
        description += f"Working hours overlap ({quality}): "
        if working_hours.get("has_overlap", False):
            hours = working_hours.get("hours", 0)
            overlap_time = working_hours.get("overlap_time", "Unknown")
            description += f"{hours} hours ({overlap_time})\n"
        else:
            description += "No overlap in standard working hours (9 AM - 5 PM)\n"
            
        description += f"Note: {working_hours.get('notes', 'No additional notes available')}"
        
        # Add meeting suggestions
        best_meeting_times = difference_data.get("best_meeting_times", [])
        if best_meeting_times:
            description += "\n\nSuggested meeting times:\n"
            for i, suggestion in enumerate(best_meeting_times, 1):
                loc1_time = suggestion.get("location1_time", "Unknown")
                loc2_time = suggestion.get("location2_time", "Unknown")
                quality = suggestion.get("quality", "Unknown")
                description += f"{i}. {location1} at {loc1_time} = {location2} at {loc2_time} ({quality})\n"
        
        return description
    
    def get_timezone_list_description(self, timezone_list_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of timezone list.
        
        Args:
            timezone_list_data (Dict[str, Any]): Timezone list data from list_timezones
            
        Returns:
            str: Human-readable timezone list description
        """
        region = timezone_list_data["region"]
        count = timezone_list_data["count"]
        timezones = timezone_list_data["timezones"]
        reference_time = timezone_list_data["reference_time"]
        
        description = f"Showing {count} timezones for {region} (as of {reference_time}):\n\n"
        
        # Group timezones by similar offset
        offset_groups = {}
        for tz in timezones:
            offset_key = tz["offset"]
            if offset_key not in offset_groups:
                offset_groups[offset_key] = []
            offset_groups[offset_key].append(tz)
        
        # Sort by offset using offset_hours (float) for reliable sorting
        sorted_offsets = sorted(offset_groups.keys(), 
                               key=lambda x: next(
                                   (tz["offset_hours"] for tz in offset_groups[x] if "offset_hours" in tz), 
                                   0
                               ))
        
        for offset in sorted_offsets:
            description += f"UTC {offset}:\n"
            for tz in offset_groups[offset]:
                dst_mark = " (DST)" if tz["dst_active"] else ""
                description += f"- {tz['name']} ({tz['abbreviation']}): {tz['current_time']}{dst_mark}\n"
            description += "\n"
        
        return description

# Functions to expose to the LLM tool system
def get_current_time(location):
    """
    Get the current time for a specified location
    
    Args:
        location (str): City name, country, or timezone identifier
        
    Returns:
        str: Current time information in natural language
    """
    try:
        print(f"get_current_time function called with location: {location}")
        tool = TimeTool()
        time_data = tool.get_current_time(location)
        description = tool.get_time_description(time_data)
        print(f"Time description generated")
        return description
    except Exception as e:
        error_msg = f"Error getting current time: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def convert_time(time_string, source_location, target_location):
    """
    Convert a time from one location to another
    
    Args:
        time_string (str): Time to convert (e.g., "2023-04-15 14:30", "3pm", "15:45")
        source_location (str): Source location or timezone
        target_location (str): Target location or timezone
        
    Returns:
        str: Converted time information in natural language
    """
    try:
        print(f"convert_time function called with time_string: {time_string}, source: {source_location}, target: {target_location}")
        tool = TimeTool()
        conversion_data = tool.convert_time(time_string, source_location, target_location)
        description = tool.get_time_conversion_description(conversion_data)
        print(f"Time conversion description generated")
        return description
    except Exception as e:
        error_msg = f"Error converting time: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_time_difference(location1, location2):
    """
    Calculate the time difference between two locations
    
    Args:
        location1 (str): First location or timezone
        location2 (str): Second location or timezone
        
    Returns:
        str: Time difference information in natural language
    """
    try:
        print(f"get_time_difference function called with locations: {location1} and {location2}")
        tool = TimeTool()
        difference_data = tool.get_time_difference(location1, location2)
        description = tool.get_time_difference_description(difference_data)
        print(f"Time difference description generated")
        return description
    except Exception as e:
        error_msg = f"Error calculating time difference: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def list_timezones(region=None):
    """
    List available timezones, optionally filtered by region
    
    Args:
        region (str, optional): Region to filter timezones (continent, country, etc.)
        
    Returns:
        str: Timezone list in natural language
    """
    try:
        print(f"list_timezones function called with region: {region}")
        tool = TimeTool()
        timezone_list_data = tool.list_timezones(region)
        description = tool.get_timezone_list_description(timezone_list_data)
        print(f"Timezone list description generated with {timezone_list_data['count']} timezones")
        return description
    except Exception as e:
        error_msg = f"Error listing timezones: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg