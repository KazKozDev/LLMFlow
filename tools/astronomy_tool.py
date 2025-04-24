import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import logging
import re
import calendar
from typing import List, Dict, Callable, Any, Optional
import ephem  # For astronomical calculations
from math import degrees
import json
from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Data structures for constellation and planet information
# ---------------------------------------------------------------------------

class Season(Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

@dataclass
class ConstellationInfo:
    name: str
    latin_name: str
    best_visible: List[Season]
    description: str
    notable_stars: List[str]
    mythology: str

@dataclass
class PlanetInfo:
    name: str
    type: str
    diameter: str  # km
    mass: str  # kg
    orbital_period: str  # Earth days/years
    rotation_period: str  # Earth days
    average_temperature: str  # Celsius
    moons: int
    rings: bool
    description: str
    interesting_facts: List[str]

# Constellation data
CONSTELLATIONS: Dict[str, ConstellationInfo] = {
    "ursa_major": ConstellationInfo(
        name="Ursa Major",
        latin_name="Ursa Major",
        best_visible=[Season.SPRING],
        description="The Great Bear, containing the Big Dipper asterism",
        notable_stars=["Alioth", "Dubhe", "Alkaid"],
        mythology="In Greek mythology, Zeus transformed his lover Callisto into a bear"
    ),
    "orion": ConstellationInfo(
        name="Orion",
        latin_name="Orion",
        best_visible=[Season.WINTER],
        description="The Hunter, one of the most recognizable constellations",
        notable_stars=["Betelgeuse", "Rigel", "Bellatrix"],
        mythology="Represents the mythical hunter Orion from Greek mythology"
    ),
    "cassiopeia": ConstellationInfo(
        name="Cassiopeia",
        latin_name="Cassiopeia",
        best_visible=[Season.AUTUMN, Season.WINTER],
        description="A distinctive W-shaped constellation representing a queen",
        notable_stars=["Schedar", "Caph", "Gamma Cassiopeiae"],
        mythology="Named after the vain queen Cassiopeia in Greek mythology"
    ),
    "scorpius": ConstellationInfo(
        name="Scorpius",
        latin_name="Scorpius",
        best_visible=[Season.SUMMER],
        description="A bright constellation resembling a scorpion",
        notable_stars=["Antares", "Shaula", "Sargas"],
        mythology="Represents the scorpion that killed Orion in Greek mythology"
    ),
    "cygnus": ConstellationInfo(
        name="Cygnus",
        latin_name="Cygnus",
        best_visible=[Season.SUMMER],
        description="The Swan, featuring the Northern Cross asterism",
        notable_stars=["Deneb", "Albireo", "Sadr"],
        mythology="Represents Zeus transformed into a swan in Greek mythology"
    ),
    "ursa_minor": ConstellationInfo(
        name="Ursa Minor",
        latin_name="Ursa Minor",
        best_visible=[Season.SPRING, Season.SUMMER],
        description="The Little Bear, containing the Little Dipper and Polaris",
        notable_stars=["Polaris", "Kochab", "Pherkad"],
        mythology="Associated with various bears in different mythologies"
    ),
    "lyra": ConstellationInfo(
        name="Lyra",
        latin_name="Lyra",
        best_visible=[Season.SUMMER],
        description="A small but distinctive constellation representing a harp",
        notable_stars=["Vega", "Sheliak", "Sulafat"],
        mythology="Represents the lyre of Orpheus in Greek mythology"
    ),
    "pegasus": ConstellationInfo(
        name="Pegasus",
        latin_name="Pegasus",
        best_visible=[Season.AUTUMN],
        description="Features the Great Square of Pegasus asterism",
        notable_stars=["Markab", "Scheat", "Algenib"],
        mythology="Named after the winged horse in Greek mythology"
    ),
    "taurus": ConstellationInfo(
        name="Taurus",
        latin_name="Taurus",
        best_visible=[Season.WINTER],
        description="The Bull, containing the Pleiades star cluster",
        notable_stars=["Aldebaran", "Elnath", "Alcyone"],
        mythology="Represents Zeus transformed into a bull in Greek mythology"
    ),
    "leo": ConstellationInfo(
        name="Leo",
        latin_name="Leo",
        best_visible=[Season.SPRING],
        description="A distinctive constellation representing a lion",
        notable_stars=["Regulus", "Denebola", "Algieba"],
        mythology="Represents the Nemean Lion slain by Hercules"
    )
}

# Planet data
PLANETS: Dict[str, PlanetInfo] = {
    "mercury": PlanetInfo(
        name="Mercury",
        type="Terrestrial planet",
        diameter="4,879",
        mass="3.285 × 10^23",
        orbital_period="88 Earth days",
        rotation_period="59 Earth days",
        average_temperature="167°C (ranging from -180°C to 430°C)",
        moons=0,
        rings=False,
        description="The smallest planet in our solar system and closest to the Sun",
        interesting_facts=[
            "Has no atmosphere and no moons",
            "Surface is heavily cratered, similar to Earth's Moon",
            "Experiences extreme temperature variations",
            "Contains ice in permanently shadowed craters at its poles"
        ]
    ),
    "venus": PlanetInfo(
        name="Venus",
        type="Terrestrial planet",
        diameter="12,104",
        mass="4.867 × 10^24",
        orbital_period="225 Earth days",
        rotation_period="243 Earth days",
        average_temperature="462°C",
        moons=0,
        rings=False,
        description="Often called Earth's sister planet due to similar size",
        interesting_facts=[
            "Rotates backwards compared to most planets",
            "Hottest planet in our solar system due to greenhouse effect",
            "Surface pressure is 90 times that of Earth",
            "Covered in thick clouds of sulfuric acid"
        ]
    ),
    "mars": PlanetInfo(
        name="Mars",
        type="Terrestrial planet",
        diameter="6,792",
        mass="6.39 × 10^23",
        orbital_period="687 Earth days",
        rotation_period="24 hours 37 minutes",
        average_temperature="-63°C",
        moons=2,
        rings=False,
        description="The Red Planet, named after the Roman god of war",
        interesting_facts=[
            "Has the largest volcano in the solar system (Olympus Mons)",
            "Shows evidence of ancient river valleys and lakes",
            "Has two small moons: Phobos and Deimos",
            "Experiences planet-wide dust storms"
        ]
    ),
    "jupiter": PlanetInfo(
        name="Jupiter",
        type="Gas giant",
        diameter="142,984",
        mass="1.898 × 10^27",
        orbital_period="11.9 Earth years",
        rotation_period="9 hours 56 minutes",
        average_temperature="-110°C",
        moons=79,
        rings=True,
        description="The largest planet in our solar system",
        interesting_facts=[
            "Has a Great Red Spot - a giant storm lasting over 400 years",
            "Strong magnetic field traps radiation in belts",
            "Has at least 79 moons, including the four large Galilean moons",
            "Emits more energy than it receives from the Sun"
        ]
    ),
    "saturn": PlanetInfo(
        name="Saturn",
        type="Gas giant",
        diameter="120,536",
        mass="5.683 × 10^26",
        orbital_period="29.5 Earth years",
        rotation_period="10 hours 42 minutes",
        average_temperature="-140°C",
        moons=82,
        rings=True,
        description="Known for its spectacular ring system",
        interesting_facts=[
            "Has the most extensive ring system of any planet",
            "Would float in a bathtub if one were large enough",
            "Has a hexagonal storm at its north pole",
            "Largest moon Titan has a thick atmosphere"
        ]
    ),
    "uranus": PlanetInfo(
        name="Uranus",
        type="Ice giant",
        diameter="51,118",
        mass="8.681 × 10^25",
        orbital_period="84 Earth years",
        rotation_period="17 hours 14 minutes",
        average_temperature="-195°C",
        moons=27,
        rings=True,
        description="The tilted planet, rotating on its side",
        interesting_facts=[
            "Rotates on its side with an axial tilt of 98 degrees",
            "First planet discovered with a telescope",
            "Appears blue-green due to methane in its atmosphere",
            "Has a system of thin, dark rings"
        ]
    ),
    "neptune": PlanetInfo(
        name="Neptune",
        type="Ice giant",
        diameter="49,244",
        mass="1.024 × 10^26",
        orbital_period="165 Earth years",
        rotation_period="16 hours 6 minutes",
        average_temperature="-200°C",
        moons=14,
        rings=True,
        description="The windiest planet, with the strongest winds in the solar system",
        interesting_facts=[
            "Has the strongest winds in the solar system (up to 2,100 km/h)",
            "Was discovered through mathematical predictions",
            "Has a dynamic atmosphere with visible storms",
            "Named after the Roman god of the sea"
        ]
    )
}

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("AstronomyTool")

# ---------------------------------------------------------------------------
# Helper functions (kept outside the class for easier unit‑testing)
# ---------------------------------------------------------------------------

def _deduplicate(items: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """Return *items* without duplicates, preserving order (first wins)."""
    seen = set()
    unique: List[Dict[str, Any]] = []
    for item in items:
        k = item.get(key)
        # Ensure k is a string before calling lower()
        if k and isinstance(k, str) and k.lower() not in seen:
            seen.add(k.lower())
            unique.append(item)
        elif k and not isinstance(k, str): # Handle non-string keys if necessary, or just skip
             # Decide how to handle non-string keys; here we just add if not seen
             if k not in seen:
                seen.add(k)
                unique.append(item)
        elif not k: # If key is missing or None, decide whether to include
             unique.append(item) # Example: include items with missing key
    return unique


def _parse_date_from_title(title: str, fallback_year: int) -> str:
    """Extract a date like "Jan 3" from *title* and append *fallback_year* if found.

    If nothing is found, return an empty string so the caller can decide what
    to do. Handles patterns like "Jan 3", "January 3", or "Jan 3/4".
    """
    # More robust regex to avoid matching year numbers as day numbers
    match = re.match(r"^(?P<month>[A-Za-z]{3,9})\s+(?P<day>[0-9]{1,2})(?:/(?P<day2>[0-9]{1,2}))?(?:,\s*(?P<year>\d{4}))?", title)
    if not match:
         # Try matching just Month Day (e.g., from NASA)
         match = re.search(r"(?P<month>[A-Za-z]{3,9})\s+(?P<day>[0-9]{1,2})", title)
         if not match:
             return "" # Really couldn't find a date pattern

    month = match.group("month")
    day = match.group("day")
    day2 = match.groupdict().get("day2") # Use get for optional groups
    year_in_title = match.groupdict().get("year")

    year_to_use = year_in_title if year_in_title else fallback_year

    # Attempt to standardize month name
    try:
        month_num = list(calendar.month_abbr).index(month[:3].title()) if len(month) >= 3 else list(calendar.month_name).index(month.title())
        month_std = calendar.month_abbr[month_num]
    except ValueError:
        month_std = month # Keep original if parsing fails

    if day2:  # e.g. "Jan 3/4" → "Jan 3‑4"
        date_str = f"{month_std} {day}-{day2}, {year_to_use}"
    else:
        date_str = f"{month_std} {day}, {year_to_use}"
    return date_str


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class AstronomyTool:
    # Tool metadata
    TOOL_NAME = "astronomy_tool"
    TOOL_DESCRIPTION = "Fetches reliable astronomical data from multiple sources with a focus on eclipses"
    """Fetches reliable astronomical data from multiple sources with a focus on eclipses."""

    # ---------------------------------------------------------------------
    # Construction & basic helpers
    # ---------------------------------------------------------------------

    def __init__(self, cache_duration: int = 3600) -> None:
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0 Safari/537.36"
            )
        }
        self.cache: Dict[str, Any] = {}
        self.cache_time: Dict[str, float] = {}
        self.cache_duration = cache_duration  # seconds

        # Pre‑defined city coordinates (lat, lon) used for rough visibility heuristics
        self.city_coordinates: Dict[str, tuple[float, float]] = {
            "barcelona": (41.3851, 2.1734),
            "madrid": (40.4168, -3.7038),
            "london": (51.5074, -0.1278),
            "paris": (48.8566, 2.3522),
            "new york": (40.7128, -74.0060),
            "tokyo": (35.6762, 139.6503),
            "sydney": (-33.8688, 151.2093),
            "moscow": (55.7558, 37.6176),
            "berlin": (52.5200, 13.4050),
            "rome": (41.9028, 12.4964),
        }

        self.fallback_data = self._load_fallback_data()

    # ---------------------------------------------------------------------
    # Public API (these methods are intended to be called by the LLM tool
    # wrapper functions defined below the class)
    # ---------------------------------------------------------------------

    def get_eclipse_info(self, location: Optional[str] = None) -> Dict[str, Any]:
        """Return structured data about upcoming eclipses (optionally filtered by *location*)."""
        cache_key = f"eclipses_{location.lower()}" if location else "eclipses_global"
        # Ensure key is created before fetching
        self.cache.setdefault(cache_key, {})
        self.cache_time.setdefault(cache_key, 0)
        return self._fetch_with_cache(cache_key, lambda: self._fetch_eclipse_data(location))


    def get_celestial_events(self, *, date: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
        """Return structured data about upcoming celestial events (optionally filtered)."""
        cache_key = f"events_{date or 'current'}_{location.lower() if location else 'global'}"
        # Ensure key is created before fetching
        self.cache.setdefault(cache_key, {})
        self.cache_time.setdefault(cache_key, 0)
        return self._fetch_with_cache(cache_key, lambda: self._fetch_celestial_events(date, location))


    # ---------------------------------------------------------------------
    # Private: Fetching helpers (with robust fall‑backs)
    # ---------------------------------------------------------------------

    def _fetch_with_cache(self, key: str, fetch_func: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """Common cache wrapper used by the public fetchers."""
        now = time.time()
        # Ensure key exists before checking time
        if key in self.cache and key in self.cache_time and (now - self.cache_time[key]) < self.cache_duration:
            logger.info("Using cached data for %s", key)
            # Ensure cached data is not empty before returning
            if self.cache[key]:
                 return self.cache[key]
            else:
                 logger.info("Cached data for %s is empty, fetching fresh data.", key)
        else:
             logger.info("Fetching fresh data for %s", key)


        try:
            data = fetch_func()
            # Only cache non-empty, valid data
            if data and (data.get("eclipses") or data.get("events")):
                 self.cache[key] = data
                 self.cache_time[key] = now
            elif key in self.cache and self.cache[key]: # If fetch failed, return old cache if exists
                 logger.warning("Fetching fresh data failed for %s, returning stale cache.", key)
                 return self.cache[key]
            else: # Fetch failed and no old cache
                 logger.error("Fetching fresh data failed for %s and no cache available. Returning empty.", key)
                 # Return a default structure to avoid errors downstream
                 data = {"error": "Failed to fetch data and no cache available.", "fetched_at": datetime.utcnow().isoformat()}
                 data["eclipses" if "eclipses" in key else "events"] = []
                 data["location"] = key.split("_")[1] if "_" in key and key.split("_")[0] in ["eclipses", "events"] else None
                 data["source"] = "Error"

        except Exception as e:
            logger.error("Exception during fetch for %s: %s. Returning empty structure.", key, e, exc_info=True)
            # Return a default error structure
            data = {"error": f"Exception during fetch: {e}", "fetched_at": datetime.utcnow().isoformat()}
            data["eclipses" if "eclipses" in key else "events"] = []
            data["location"] = key.split("_")[1] if "_" in key and key.split("_")[0] in ["eclipses", "events"] else None
            data["source"] = "Error"

        return data


    def _safe_request(self, url: str, *, timeout: int = 15) -> Optional[requests.Response]: # Increased timeout
        """HTTP GET wrapper that never raises; returns *None* on failure."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=timeout)
            resp.raise_for_status()  # Check for HTTP errors like 404, 500
            # Basic check for empty or minimal content
            if not resp.text or len(resp.text) < 100:
                 logger.warning("Request successful but content seems empty or too short for %s", url)
                 # Optionally return None here, or let parsing handle it
                 # return None
            logger.info("Request successful for %s", url)
            return resp
        except requests.exceptions.Timeout:
             logger.warning("Request timed out for %s after %d seconds", url, timeout)
             return None
        except requests.exceptions.RequestException as exc:  # Catch specific request errors
            logger.warning("Request failed for %s: %s", url, exc)
            return None
        except Exception as exc: # Catch other potential errors (less likely)
            logger.error("An unexpected error occurred during request for %s: %s", url, exc, exc_info=True)
            return None

    # ---------------------------------------------------------------------
    # Core scraping logic (eclipses & other events)
    # ---------------------------------------------------------------------

    def _fetch_eclipse_data(self, location: Optional[str]) -> Dict[str, Any]:
        """Internal worker fetching eclipse information with multiple fall‑backs."""
        eclipses: List[Dict[str, Any]] = []
        source = "Unknown"
        current_year = datetime.utcnow().year

        try:
            # 1) Primary source: timeanddate list page ----------------------------------
            tad_url = "https://www.timeanddate.com/eclipse/list.html"
            logger.info("Attempting to fetch eclipses from TimeAndDate: %s", tad_url)
            resp = self._safe_request(tad_url)
            if resp:
                soup = BeautifulSoup(resp.text, "html.parser")
                table = soup.find("table", class_="table")
                if table:
                    rows = table.find_all("tr")
                    logger.info("Found %d rows in TimeAndDate eclipse table.", len(rows))
                    for row in rows[1:]:  # skip header row
                        cols = row.find_all("td")
                        if len(cols) >= 5: # Need at least 5 columns
                            try:
                                date_raw = cols[0].get_text(strip=True)
                                eclipse_type_raw = cols[1].get_text(strip=True)
                                # Clean up type description (e.g., remove 'Upcoming')
                                eclipse_type = re.sub(r'\bUpcoming\b', '', eclipse_type_raw, flags=re.IGNORECASE).strip()
                                visibility_raw = cols[4].get_text(strip=True)
                                link_tag = cols[1].find("a")
                                details_link = (
                                    f"https://www.timeanddate.com{link_tag['href']}" if link_tag and link_tag.get("href") else None
                                )

                                # Basic date parsing/validation if possible
                                parsed_date = ""
                                try:
                                     # Attempt to parse date like "18 Sep 2024" or "12 Aug 2026"
                                     dt_obj = datetime.strptime(date_raw, "%d %b %Y")
                                     parsed_date = dt_obj.strftime("%B %d, %Y") # Standardize format
                                except ValueError:
                                     parsed_date = date_raw # Keep original if parse fails

                                # Filter out past eclipses if date parsing worked
                                if parsed_date and parsed_date != date_raw: # Check if parsing worked
                                    try:
                                        if dt_obj.date() < datetime.utcnow().date():
                                             logger.debug("Skipping past eclipse: %s", parsed_date)
                                             continue # Skip past eclipses
                                    except NameError: # dt_obj might not be defined if parsing failed
                                         pass

                                eclipses.append(
                                    {
                                        "type": eclipse_type,
                                        "date": parsed_date, # Use parsed/standardized date
                                        "visibility": visibility_raw,
                                        "details_link": details_link,
                                        "source": "TimeAndDate.com"
                                    }
                                )
                            except IndexError:
                                logger.warning("Skipping row due to insufficient columns: %s", row.prettify())
                            except Exception as e:
                                logger.warning("Error parsing row in TimeAndDate: %s - %s", e, row.prettify())
                    if eclipses:
                        source = "TimeAndDate.com"
                        logger.info("Successfully parsed %d eclipses from TimeAndDate.", len(eclipses))
                else:
                    logger.warning("Could not find eclipse table on TimeAndDate page.")
            else:
                logger.warning("Failed to fetch data from TimeAndDate.")


            # 2) Secondary source: NASA catalogue (only if primary failed or empty) -----
            # Note: NASA pages are often structured by year ranges. Need to find current/future ones.
            # This example uses a fixed URL, which will become outdated. A more robust solution
            # would dynamically find the correct NASA page, but that's more complex.
            if not eclipses:
                nasa_base_url = "https://eclipse.gsfc.nasa.gov/SEgoogle/"
                # Try a couple of potential year ranges
                nasa_urls = [
                     f"{nasa_base_url}SEgoogle{current_year-1}to{current_year+4}.html", # Wider range
                     f"{nasa_base_url}SEgoogle{current_year}to{current_year+1}.html", # Narrower range
                     "https://eclipse.gsfc.nasa.gov/SEgoogle/SEgoogle2021.html" # Original fallback (likely outdated)
                ]
                nasa_found = False
                for nasa_url in nasa_urls:
                     if nasa_found: break # Stop if we found data
                     logger.info("Attempting to fetch eclipses from NASA: %s", nasa_url)
                     resp = self._safe_request(nasa_url)
                     if resp:
                         soup = BeautifulSoup(resp.text, "html.parser")
                         # NASA uses links with specific patterns for eclipses
                         eclipse_links = soup.find_all('a', href=re.compile(r"SEplot(m|p|)?/\d{4}\w+\.gif")) # Pattern for eclipse plots
                         if not eclipse_links: # Fallback: Look for headers if links fail
                              eclipse_elements = soup.find_all(["h2", "h3"], string=re.compile(r"eclipse", re.IGNORECASE))
                         else:
                              eclipse_elements = eclipse_links # Use links if found

                         logger.info("Found %d potential eclipse elements on NASA page %s.", len(eclipse_elements), nasa_url)

                         for element in eclipse_elements:
                             try:
                                 # Try to find the nearest date information
                                 # This depends heavily on NASA's page structure
                                 parent_section = element.find_parent('p') or element.find_parent('div') or element # Look upwards for context
                                 text_content = parent_section.get_text(" ", strip=True) if parent_section else element.get_text(" ", strip=True)

                                 date_match = re.search(r"(\d{4})\s+([A-Za-z]{3,9})\s+(\d{1,2})", text_content) # YYYY Mon DD
                                 if not date_match:
                                      date_match = re.search(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", text_content) # Mon DD, YYYY
                                 if not date_match:
                                      logger.debug("Could not find date near element: %s", element.get_text())
                                      continue # Skip if no date found nearby

                                 # Extract and format date
                                 if len(date_match.groups()) == 3:
                                      if date_match.group(1).isdigit(): # YYYY Mon DD format
                                          year, month_str, day = date_match.groups()
                                      else: # Mon DD, YYYY format
                                          month_str, day, year = date_match.groups()

                                      try:
                                           dt_obj = datetime.strptime(f"{year} {month_str[:3]} {day}", "%Y %b %d")
                                           date_raw = dt_obj.strftime("%B %d, %Y") # Standardize
                                           # Filter out past eclipses
                                           if dt_obj.date() < datetime.utcnow().date():
                                               logger.debug("Skipping past NASA eclipse: %s", date_raw)
                                               continue
                                      except ValueError:
                                           logger.warning("Could not parse NASA date: %s", date_match.group(0))
                                           continue # Skip if date is invalid
                                 else:
                                      logger.warning("Date match format unexpected: %s", date_match.group(0))
                                      continue

                                 # Determine type (best guess from surrounding text)
                                 lc_text = text_content.lower()
                                 eclipse_type = "Eclipse" # Generic default
                                 if "total solar" in lc_text: eclipse_type = "Total Solar Eclipse"
                                 elif "annular solar" in lc_text: eclipse_type = "Annular Solar Eclipse"
                                 elif "hybrid solar" in lc_text: eclipse_type = "Hybrid Solar Eclipse"
                                 elif "partial solar" in lc_text: eclipse_type = "Partial Solar Eclipse"
                                 elif "total lunar" in lc_text: eclipse_type = "Total Lunar Eclipse"
                                 elif "partial lunar" in lc_text: eclipse_type = "Partial Lunar Eclipse"
                                 elif "penumbral lunar" in lc_text: eclipse_type = "Penumbral Lunar Eclipse"
                                 elif "solar" in lc_text: eclipse_type = "Solar Eclipse" # Broader fallback
                                 elif "lunar" in lc_text: eclipse_type = "Lunar Eclipse" # Broader fallback

                                 # Visibility: NASA pages often don't have a simple summary string.
                                 # Link to the map is the best bet.
                                 details_link = None
                                 if element.name == 'a' and element.get('href'):
                                      details_link = requests.compat.urljoin(nasa_url, element['href']) # Make URL absolute
                                 visibility = f"See map/details at NASA link ({element.get_text(strip=True)})" if details_link else "Visibility details require checking NASA page."

                                 eclipses.append(
                                     {
                                         "type": eclipse_type,
                                         "date": date_raw,
                                         "visibility": visibility,
                                         "details_link": details_link,
                                         "source": "NASA GSFC"
                                     }
                                 )
                                 nasa_found = True # Mark that we found data on this URL
                             except Exception as e:
                                 logger.warning("Error parsing NASA element: %s - Element: %s", e, element.prettify()[:200]) # Log element start

                         if eclipses:
                             source = "NASA GSFC"
                             logger.info("Successfully parsed %d eclipses from NASA %s.", len(eclipses), nasa_url)
                         else:
                             logger.info("No future eclipses found on NASA page %s.", nasa_url)
                     else:
                         logger.warning("Failed to fetch data from NASA URL: %s", nasa_url)


            # 3) Fall‑back static data --------------------------------------------------
            if not eclipses:
                logger.warning("Failed to fetch from primary and secondary sources. Using fallback eclipse data.")
                eclipses = self.fallback_data["eclipses"]
                source = "Fallback Data"
                # Add source to fallback items if missing
                for item in eclipses:
                    item.setdefault("source", source)

            # 4) Deduplicate based on Date and Type (best effort)
            unique_eclipses = []
            seen_eclipses = set()
            for eclipse in eclipses:
                 # Normalize date for comparison if possible, otherwise use raw string
                 date_key = eclipse.get('date', '')
                 type_key = eclipse.get('type', '').split(" ")[0] # Use first word of type (Total, Partial, Annular)
                 composite_key = f"{date_key}_{type_key}".lower()
                 if composite_key not in seen_eclipses:
                      unique_eclipses.append(eclipse)
                      seen_eclipses.add(composite_key)
                 else:
                      logger.debug("Skipping duplicate eclipse: %s", composite_key)
            eclipses = unique_eclipses


            # 5) Filter/prioritise by location ----------------------------------------
            filtered_eclipses = eclipses # Default to all if no location specified
            if location:
                logger.info("Filtering eclipses for location: %s", location)
                filtered_eclipses = self._filter_eclipses_by_location(eclipses, location)

            return {
                "eclipses": filtered_eclipses,
                "location": location,
                "source": source,
                "fetched_at": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.error("Error fetching eclipses: %s", exc, exc_info=True)
            # Return fallback data in case of unexpected error during processing
            fallback = self.fallback_data["eclipses"]
            for item in fallback: item.setdefault("source", "Fallback Data (after exception)")
            return {
                "eclipses": self._filter_eclipses_by_location(fallback, location) if location else fallback,
                "location": location,
                "source": "Fallback Data (after exception)",
                "fetched_at": datetime.utcnow().isoformat(),
                "error": f"An exception occurred: {exc}"
            }

    # .................................................................................

    def _fetch_celestial_events(self, date: Optional[str], location: Optional[str]) -> Dict[str, Any]:
        """Fetch celestial events other than eclipses, repairing earlier date/duplication bugs."""
        events: List[Dict[str, Any]] = []
        source = "Unknown"
        current_year = datetime.utcnow().year
        current_month_name = calendar.month_name[datetime.utcnow().month]

        try:
            # ---------------------------------------------------------------------
            # Strategy A – TimeAndDate "sights‑to‑see"
            # ---------------------------------------------------------------------
            tad_url = "https://www.timeanddate.com/astronomy/sights-to-see.html"
            logger.info("Attempting to fetch celestial events from TimeAndDate: %s", tad_url)
            resp = self._safe_request(tad_url)
            if resp:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for sections, often marked by <article> or divs with specific classes
                event_elements = soup.select('article, .panel.panel--astro.panel--fixed') # Adjust selector based on current site structure

                logger.info("Found %d potential event elements on TimeAndDate.", len(event_elements))

                for element in event_elements:
                    try:
                        # Extract title (will often contain the date prefix) --------------
                        # Prioritize more specific headers first
                        title_tag = element.find(["h2", "h3", "h4"]) or element.find("strong")
                        if not title_tag:
                            # Maybe the title is in a link within a standard structure
                            link_title = element.select_one('a > h3') or element.select_one('a > strong')
                            title_tag = link_title if link_title else None

                        if not title_tag:
                            logger.debug("Skipping element, no title tag found.")
                            continue
                        title_text = title_tag.get_text(strip=True)

                        # Description ----------------------------------------------------
                        desc_tag = element.find("p")
                        description = desc_tag.get_text(strip=True) if desc_tag else "No description available."
                        # Sometimes the description is empty or just repeats title, clean up
                        if not description or description.lower() == title_text.lower():
                             # Look for sibling p tags or other common description locations
                             next_p = title_tag.find_next_sibling("p")
                             if next_p: description = next_p.get_text(strip=True)
                             if not description or description.lower() == title_text.lower():
                                  description = "See source for details." # Fallback description


                        # Date Parsing Logic ------------------------------------------
                        event_date = ""
                        # Date (1) – explicit <time> tag -------------------------------
                        time_tag = element.find("time")
                        if time_tag and time_tag.get("datetime"):
                            datetime_str = time_tag["datetime"]
                            try:
                                # Handle full datetime or just date
                                if 'T' in datetime_str:
                                    dt_obj = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
                                    event_date = dt_obj.strftime("%Y-%m-%d") # ISO date for consistency
                                else:
                                    dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d")
                                    event_date = dt_obj.strftime("%B %d, %Y") # Format as "Month Day, Year"
                            except ValueError:
                                logger.warning("Could not parse datetime '%s' from <time> tag.", datetime_str)
                                event_date = datetime_str # Fallback to raw value if parsing fails

                        # Date (2) – parse from title (if <time> failed) ----------
                        if not event_date:
                            event_date = _parse_date_from_title(title_text, current_year)

                        # Date (3) – Fallback using Month Name if still no date ----
                        if not event_date:
                            # Extract month from headers or context if possible
                            month_header = element.find_previous(["h2", "h3"], string=re.compile(r"|".join(calendar.month_name[1:])))
                            month_context = current_month_name # Default to current month
                            if month_header:
                                 match = re.search(r"|".join(calendar.month_name[1:]), month_header.get_text(), re.IGNORECASE)
                                 if match: month_context = match.group(0)

                            event_date = f"{month_context} {current_year} (approximate)" # Mark as approximate
                            logger.debug("Falling back to approximate date for event: %s", title_text)


                        # Determine rough type -------------------------------------------
                        lc_title = title_text.lower()
                        lc_desc = description.lower()
                        event_type = "other" # Default
                        if "eclipse" in lc_title or "eclipse" in lc_desc:
                            event_type = "eclipse"
                        elif "meteor shower" in lc_title or "meteor shower" in lc_desc:
                            event_type = "meteor shower"
                        elif "solstice" in lc_title:
                            event_type = "solstice"
                        elif "equinox" in lc_title:
                            event_type = "equinox"
                        elif "elongation" in lc_title:
                            event_type = "elongation"
                        elif "conjunction" in lc_title:
                             event_type = "conjunction"
                        elif "opposition" in lc_title:
                             event_type = "opposition"
                        elif "moon phase" in lc_title or "full moon" in lc_title or "new moon" in lc_title:
                             event_type = "moon phase"


                        # Add to list if title seems valid
                        if title_text and title_text != description:
                            events.append(
                                {
                                    "name": title_text,
                                    "date": event_date,
                                    "description": description,
                                    "type": event_type,
                                    "source": "TimeAndDate.com"
                                }
                            )
                    except Exception as e:
                        logger.warning("Error parsing TimeAndDate event element: %s - Element: %s", e, element.prettify()[:200])

                if events:
                    source = "TimeAndDate.com"
                    logger.info("Successfully parsed %d events from TimeAndDate.", len(events))
                else:
                     logger.warning("Could not parse any events from TimeAndDate structure.")

            else:
                 logger.warning("Failed to fetch celestial events from TimeAndDate.")


            # ---------------------------------------------------------------------
            # Strategy B – In‑The‑Sky calendar (backup)
            # ---------------------------------------------------------------------
            if not events:
                its_url = "https://in-the-sky.org/newscalendar.php"
                logger.info("Attempting to fetch celestial events from In-The-Sky.org: %s", its_url)
                resp = self._safe_request(its_url)
                if resp:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Target the main table containing events
                    event_table = soup.find('table', attrs={'width': '100%', 'cellpadding': '12'})
                    if event_table:
                        rows = event_table.find_all("tr") # Get all rows within that table
                        logger.info("Found %d rows in In-The-Sky event table.", len(rows))
                        for row in rows:
                            try:
                                # Expecting two cells per event row: Date | Description
                                cells = row.find_all('td')
                                if len(cells) == 2:
                                    date_cell = cells[0]
                                    desc_cell = cells[1]

                                    # Extract date - usually in a link or span
                                    date_tag = date_cell.find('a') or date_cell.find('span')
                                    date_text = date_tag.get_text(strip=True) if date_tag else date_cell.get_text(strip=True)
                                    # Attempt to parse/standardize date
                                    event_date = _parse_date_from_title(date_text, current_year)
                                    if not event_date: # Fallback if parsing fails
                                         event_date = date_text if date_text else f"{current_month_name} {current_year} (approximate)"


                                    # Extract description/title - usually in a link
                                    title_tag = desc_cell.find('a')
                                    title_text = title_tag.get_text(strip=True) if title_tag else desc_cell.get_text(strip=True)

                                    # Description might be the title itself or need fallback
                                    description = title_text

                                    # Determine type (basic check)
                                    lc_title = title_text.lower()
                                    event_type = "eclipse" if "eclipse" in lc_title else "other"
                                    if "meteor shower" in lc_title: event_type = "meteor shower" # Add more types if needed

                                    events.append(
                                        {
                                            "name": title_text,
                                            "date": event_date,
                                            "description": description, # Using title as description for this source
                                            "type": event_type,
                                            "source": "In-The-Sky.org"
                                        }
                                    )
                                else:
                                    # logger.debug("Skipping row, expected 2 cells, found %d: %s", len(cells), row.prettify()[:100])
                                    pass # Skip header/separator rows quietly

                            except Exception as e:
                                logger.warning("Error parsing In-The-Sky row: %s - Row: %s", e, row.prettify()[:200])

                        if events:
                            source = "In-The-Sky.org"
                            logger.info("Successfully parsed %d events from In-The-Sky.org.", len(events))
                        else:
                             logger.warning("Could not parse any events from In-The-Sky.org structure.")
                    else:
                         logger.warning("Could not find main event table on In-The-Sky.org page.")
                else:
                     logger.warning("Failed to fetch celestial events from In-The-Sky.org.")


            # ---------------------------------------------------------------------
            # Final fall‑back – static list if everything failed
            # ---------------------------------------------------------------------
            if not events:
                logger.warning("Fetching from web sources failed. Using fallback celestial events data.")
                events = self.fallback_data["celestial_events"]
                source = "Fallback Data"
                # Add source to fallback items if missing
                for item in events:
                    item.setdefault("source", source)


            # Deduplicate & keep order ------------------------------------------------
            # Use a combination of name and date for deduplication key
            logger.info("Deduplicating %d fetched events.", len(events))
            unique_events = []
            seen_events = set()
            for event in events:
                 name_key = event.get('name', 'Unknown Event')
                 date_key = event.get('date', 'Unknown Date').split(',')[0] # Use date part before year for flexibility
                 composite_key = f"{name_key}_{date_key}".lower()
                 if composite_key not in seen_events:
                      unique_events.append(event)
                      seen_events.add(composite_key)
                 else:
                      logger.debug("Skipping duplicate event: %s", composite_key)
            events = unique_events
            logger.info("Found %d unique events after deduplication.", len(events))


            # Filter by date if specified (basic string matching for now)
            if date:
                 logger.info("Filtering events for date: %s", date)
                 date_lc = date.lower()
                 events = [ev for ev in events if date_lc in ev.get('date', '').lower()]
                 logger.info("Found %d events matching date filter.", len(events))


            # Note: Location filtering for general celestial events is tricky without precise coordinates/times.
            # We are currently *not* filtering general events by location.

            return {
                "events": events,
                "location": location, # Keep location even if not used for filtering general events
                "source": source,
                "fetched_at": datetime.utcnow().isoformat(),
            }
        except Exception as exc:
            logger.error("Error fetching celestial events: %s", exc, exc_info=True)
            fallback = self.fallback_data["celestial_events"]
            for item in fallback: item.setdefault("source", "Fallback Data (after exception)")
            return {
                "events": fallback,
                "location": location,
                "source": "Fallback Data (after exception)",
                "fetched_at": datetime.utcnow().isoformat(),
                "error": f"An exception occurred: {exc}"
            }

    # ---------------------------------------------------------------------
    # Location‑specific helper for eclipses
    # ---------------------------------------------------------------------

    def _filter_eclipses_by_location(self, eclipses: List[Dict[str, Any]], location: str) -> List[Dict[str, Any]]:
        """Filters and reorders eclipses based on likely visibility in *location*."""
        if not location:
            return eclipses # No location, return all

        location_lc = location.lower()
        loc_eclipses: List[Dict[str, Any]] = []
        maybe_eclipses: List[Dict[str, Any]] = [] # For hemisphere/continent matches
        others: List[Dict[str, Any]] = []

        logger.info("Applying location filter for '%s' to %d eclipses.", location, len(eclipses))

        for eclipse in eclipses:
            vis = eclipse.get("visibility", "").lower()
            ecl_type = eclipse.get("type", "").lower()

            # 1. Direct Match (City/Country Name)
            if location_lc in vis:
                logger.debug("Direct location match for '%s' in: %s", location, vis)
                loc_eclipses.append(eclipse)
                continue

            # 2. Continent/Major Region Match
            # Add more regions as needed
            regions = ["europe", "asia", "africa", "north america", "south america", "australia", "pacific", "atlantic", "antarctica"]
            matched_region = False
            for region in regions:
                 if region in vis:
                      # Check if the location likely belongs to this region (simple check)
                      # This needs a better location-to-region mapping for accuracy
                      # Example heuristic:
                      if (location_lc in ["barcelona", "madrid", "london", "paris", "berlin", "rome", "moscow"] and region in ["europe", "atlantic"]) or \
                         (location_lc == "new york" and region in ["north america", "atlantic"]) or \
                         (location_lc == "tokyo" and region in ["asia", "pacific"]) or \
                         (location_lc == "sydney" and region in ["australia", "pacific"]):
                           logger.debug("Region match (%s) for '%s' in: %s", region, location, vis)
                           maybe_eclipses.append(eclipse)
                           matched_region = True
                           break
            if matched_region:
                 continue


            # 3. Simple hemisphere heuristic if coordinates known
            if location_lc in self.city_coordinates:
                lat, _ = self.city_coordinates[location_lc]
                hemi_tag = "north" if lat >= 0 else "south" # Match "north" or "south"
                # Check for hemisphere mentions, avoiding "south america" etc. directly
                if (f" {hemi_tag}" in vis or f"{hemi_tag}ern" in vis or vis.startswith(hemi_tag)) and not any(r in vis for r in ["south america", "north america"]):
                     logger.debug("Hemisphere match (%s) for '%s' in: %s", hemi_tag, location, vis)
                     maybe_eclipses.append(eclipse)
                     continue

            # 4. If none of the above, add to others
            others.append(eclipse)

        # Prioritize direct matches, then regional/hemisphere, then others
        result = loc_eclipses + maybe_eclipses + others
        logger.info("Filtering result: %d direct, %d maybe, %d others.", len(loc_eclipses), len(maybe_eclipses), len(others))
        return result

    def get_visible_constellations_data(self, location: Optional[str] = None, date: Optional[str] = None) -> Dict[str, Any]:
        """Return structured data about visible constellations for a location and date."""
        try:
            # Parse date or use current date
            if date and date.lower() == 'tonight':
                target_date = ephem.Date(datetime.utcnow())
            elif date:
                try:
                    target_date = ephem.Date(datetime.strptime(date, "%Y-%m-%d"))
                except ValueError:
                    logger.warning("Invalid date format '%s', using current date", date)
                    target_date = ephem.Date(datetime.utcnow())
            else:
                target_date = ephem.Date(datetime.utcnow())

            # Get coordinates for location
            lat, lon = None, None
            if location:
                location_lower = location.lower()
                if location_lower in self.city_coordinates:
                    lat, lon = self.city_coordinates[location_lower]
                else:
                    # Try to fetch coordinates using geolocation tool
                    try:
                        from geolocation_tool import get_location_info
                        geo_info = get_location_info(location)
                        if isinstance(geo_info, dict):
                            lat = geo_info.get('latitude')
                            lon = geo_info.get('longitude')
                    except (ImportError, Exception) as e:
                        logger.warning("Could not get coordinates for location '%s': %s", location, e)

            if not lat or not lon:
                logger.warning("No coordinates available for location '%s', using default (London)", location)
                lat, lon = self.city_coordinates["london"]  # Default to London

            # Create observer
            observer = ephem.Observer()
            observer.lat = str(lat)
            observer.lon = str(lon)
            observer.date = target_date
            observer.elevation = 0

            # Calculate current season
            month = observer.date.datetime().month
            if 3 <= month <= 5:
                current_season = Season.SPRING
            elif 6 <= month <= 8:
                current_season = Season.SUMMER
            elif 9 <= month <= 11:
                current_season = Season.AUTUMN
            else:
                current_season = Season.WINTER

            # Get visible constellations
            visible_constellations = []
            for const_key, const_info in CONSTELLATIONS.items():
                # Check if constellation is best visible in current season
                seasonal_visibility = current_season in const_info.best_visible

                # Calculate rough visibility based on time and location
                # This is a simplified check - real astronomical calculations would be more complex
                visible_constellations.append({
                    "name": const_info.name,
                    "latin_name": const_info.latin_name,
                    "description": const_info.description,
                    "notable_stars": const_info.notable_stars,
                    "mythology": const_info.mythology,
                    "seasonal_visibility": seasonal_visibility,
                    "best_viewing_time": "Evening" if seasonal_visibility else "Variable"
                })

            return {
                "constellations": visible_constellations,
                "location": location,
                "coordinates": {"latitude": lat, "longitude": lon},
                "date": observer.date.datetime().strftime("%Y-%m-%d"),
                "season": current_season.value,
                "fetched_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error("Error getting constellation data: %s", e, exc_info=True)
            return {
                "error": f"Failed to calculate visible constellations: {str(e)}",
                "location": location,
                "date": date,
                "fetched_at": datetime.utcnow().isoformat()
            }

    def get_planet_data(self, planet: str) -> Dict[str, Any]:
        """Return structured data about a specific planet."""
        try:
            # Clean and validate planet name
            if not planet:
                raise ValueError("No planet name provided")
            
            planet_lower = planet.lower().strip()
            if planet_lower not in PLANETS:
                raise ValueError(f"Unknown planet: {planet}")

            planet_info = PLANETS[planet_lower]

            # Calculate current position using ephem
            ephem_planet = getattr(ephem, planet_info.name)()
            ephem_planet.compute()

            # Get current distance from Earth
            distance_au = ephem_planet.earth_distance
            distance_km = distance_au * 149597870.7  # Convert AU to km

            # Get constellation the planet is currently in
            constellation = ephem.constellation(ephem_planet)[1]

            # Get magnitude (brightness)
            magnitude = ephem_planet.mag

            # Get phase (percentage illuminated)
            phase = ephem_planet.phase

            return {
                "info": {
                    "name": planet_info.name,
                    "type": planet_info.type,
                    "diameter": planet_info.diameter,
                    "mass": planet_info.mass,
                    "orbital_period": planet_info.orbital_period,
                    "rotation_period": planet_info.rotation_period,
                    "average_temperature": planet_info.average_temperature,
                    "moons": planet_info.moons,
                    "rings": planet_info.rings,
                    "description": planet_info.description,
                    "interesting_facts": planet_info.interesting_facts
                },
                "current_data": {
                    "distance_from_earth": {
                        "au": round(distance_au, 3),
                        "km": f"{distance_km:,.0f}"
                    },
                    "constellation": constellation,
                    "magnitude": round(magnitude, 2),
                    "phase": round(phase, 1),
                    "observable": magnitude < 6.0  # Visible to naked eye if magnitude < 6
                },
                "fetched_at": datetime.utcnow().isoformat()
            }

        except ValueError as ve:
            logger.warning("Value error in get_planet_data: %s", ve)
            return {
                "error": str(ve),
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error("Error getting planet data: %s", e, exc_info=True)
            return {
                "error": f"Failed to get planet information: {str(e)}",
                "fetched_at": datetime.utcnow().isoformat()
            }

    @staticmethod
    def format_visible_constellations(data: Dict[str, Any]) -> str:
        """Format constellation data into a user-readable string."""
        if not data or "error" in data:
            error_msg = data.get('error', 'Could not retrieve constellation information.')
            logger.error("format_visible_constellations called with error data: %s", error_msg)
            return f"Error retrieving constellation information: {error_msg}"

        constellations = data.get("constellations", [])
        location = data.get("location", "Unknown location")
        date = data.get("date", "Unknown date")
        season = data.get("season", "Unknown season")
        coords = data.get("coordinates", {})

        header = f"Visible Constellations for {location}"
        if coords:
            header += f" (Lat: {coords['latitude']:.2f}°, Lon: {coords['longitude']:.2f}°)"
        header += f"\nDate: {date} ({season})\n"

        if not constellations:
            return header + "\nNo constellation data available for this location and time."

        body_lines = []
        for const in constellations:
            body_lines.append(f"\n• {const['name']} ({const['latin_name']})")
            body_lines.append(f"  Description: {const['description']}")
            if const['notable_stars']:
                body_lines.append(f"  Notable stars: {', '.join(const['notable_stars'])}")
            if const['mythology']:
                body_lines.append(f"  Mythology: {const['mythology']}")
            body_lines.append(f"  Best viewing: {const['best_viewing_time']}")

        footer = f"\nFetched at: {datetime.fromisoformat(data['fetched_at']).strftime('%Y-%m-%d %H:%M UTC')}"
        
        return header + "\n".join(body_lines) + footer

    @staticmethod
    def format_planet_info(data: Dict[str, Any]) -> str:
        """Format planet data into a user-readable string."""
        if not data or "error" in data:
            error_msg = data.get('error', 'Could not retrieve planet information.')
            logger.error("format_planet_info called with error data: %s", error_msg)
            return f"Error retrieving planet information: {error_msg}"

        info = data.get("info", {})
        current = data.get("current_data", {})
        
        if not info:
            return "No planet information available."

        # Basic information
        lines = [
            f"{info['name']} - {info['type']}",
            f"\nPhysical Characteristics:",
            f"• Diameter: {info['diameter']} km",
            f"• Mass: {info['mass']} kg",
            f"• Average Temperature: {info['average_temperature']}",
            f"• Orbital Period: {info['orbital_period']}",
            f"• Rotation Period: {info['rotation_period']}",
            f"\nOther Features:",
            f"• Number of Known Moons: {info['moons']}",
            f"• Ring System: {'Yes' if info['rings'] else 'No'}",
            f"\nDescription:",
            info['description']
        ]

        # Current observational data
        if current:
            lines.extend([
                f"\nCurrent Observational Data:",
                f"• Distance from Earth: {current['distance_from_earth']['au']} AU ({current['distance_from_earth']['km']} km)",
                f"• Currently in constellation: {current['constellation']}",
                f"• Brightness (magnitude): {current['magnitude']}",
                f"• Phase: {current['phase']}% illuminated",
                f"• Visible to naked eye: {'Yes' if current['observable'] else 'No'}"
            ])

        # Interesting facts
        if info['interesting_facts']:
            lines.append("\nInteresting Facts:")
            for fact in info['interesting_facts']:
                lines.append(f"• {fact}")

        # Add fetch timestamp
        lines.append(f"\nFetched at: {datetime.fromisoformat(data['fetched_at']).strftime('%Y-%m-%d %H:%M UTC')}")

        return "\n".join(lines)

    @staticmethod
    def format_eclipse_info(data: Dict[str, Any]) -> str:
        """Formats eclipse data into a user-readable string."""
        if not data or "error" in data:
            error_msg = data.get('error', 'Could not retrieve eclipse information.')
            logger.error("format_eclipse_info called with error data: %s", error_msg)
            return f"Error retrieving eclipse information: {error_msg}"

        eclipses = data.get("eclipses", [])
        location = data.get("location")
        source = data.get("source", "Unknown")
        fetched_at = data.get("fetched_at", "Unknown")

        header = "Upcoming Eclipses"
        if location:
            header += f" potentially visible from {location.title()}" # Title case location
        header += ":\n"

        if not eclipses:
            body = "\nNo upcoming eclipses found"
            if location:
                 body += f" matching the visibility criteria for {location.title()}."
            else:
                 body += "."
            body += "\n"
        else:
            body_lines: List[str] = []
            for i, ecl in enumerate(eclipses):
                 ecl_type = ecl.get('type', 'Eclipse')
                 ecl_date = ecl.get('date', 'Date unknown')
                 visibility = ecl.get('visibility', 'Visibility details not available.')
                 details_link = ecl.get('details_link')

                 body_lines.append(f"• {ecl_type.title()}") # Title case type
                 body_lines.append(f"  Date: {ecl_date}")
                 # Add visibility if it's not just a generic placeholder from NASA link
                 if visibility and "See map/details at NASA link" not in visibility:
                     body_lines.append(f"  Visibility: {visibility}")
                 elif details_link: # If NASA link exists, mention it instead of generic visibility
                      body_lines.append(f"  Visibility: Check NASA map/details.")

                 if details_link:
                     body_lines.append(f"  More info: {details_link}")
                 body_lines.append("")  # Blank line between eclipses

                 # Limit output length slightly if too many results
                 if i >= 9 and len(eclipses) > 10: # Show first 10 if many results
                     body_lines.append(f"... and {len(eclipses) - 10} more.")
                     break

            body = "\n" + "\n".join(body_lines)

        # Format fetched_at timestamp nicely
        try:
            if fetched_at != "Unknown":
                fetched_dt = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
                # Format like "YYYY-MM-DD HH:MM UTC"
                fetched_str = fetched_dt.strftime("%Y-%m-%d %H:%M UTC")
            else:
                fetched_str = "Unknown"
        except ValueError:
             fetched_str = fetched_at # Keep original if parsing fails


        footer = (
            f"\nSource: {source}\n"
            f"Last updated: {fetched_str}"
        )
        return header + body + footer

    @staticmethod
    def format_celestial_events(data: Dict[str, Any]) -> str:
        """Formats general celestial event data into a user-readable string."""
        if not data or "error" in data:
            error_msg = data.get('error', 'Could not retrieve celestial event information.')
            logger.error("format_celestial_events called with error data: %s", error_msg)
            return f"Error retrieving celestial event information: {error_msg}"

        events = data.get("events", [])
        location = data.get("location")
        source = data.get("source", "Unknown")
        fetched_at = data.get("fetched_at", "Unknown")

        header = "Upcoming Celestial Events"
        header += ":\n"

        if not events:
            body = "\nNo upcoming celestial events found.\n"
        else:
            body_lines: List[str] = []
            for ev in events:
                name = ev.get("name", "N/A")
                date = ev.get("date", "N/A")
                description = ev.get("description", "")

                body_lines.append(f"• {name.title()}")
                body_lines.append(f"  Date: {date}")

                if description and description.strip() and description.lower() != name.lower():
                    body_lines.append(f"  {description.capitalize()}")

                event_source = ev.get("source")
                if event_source and event_source != source:
                     body_lines.append(f"  (Source: {event_source})")

                body_lines.append("")

            body = "\n" + "\n".join(body_lines)

        try:
            if fetched_at != "Unknown":
                fetched_dt = datetime.fromisoformat(fetched_at.replace('Z', '+00:00'))
                fetched_str = fetched_dt.strftime("%Y-%m-%d %H:%M UTC")
            else:
                fetched_str = "Unknown"
        except ValueError:
             fetched_str = fetched_at

        footer = (
            f"\nSource: {source}\n"
            f"Last updated: {fetched_str}"
        )
        return header + body + footer


    # ---------------------------------------------------------------------
    # Static fall‑back data
    # ---------------------------------------------------------------------

    @staticmethod
    def _load_fallback_data() -> Dict[str, Any]:
        """Loads static fallback data."""
        # IMPORTANT: Update fallback dates periodically or make them relative
        # For demonstration, using fixed future dates relative to a hypothetical 'today'.
        # In a real scenario, these should be updated or generated dynamically.
        current_year = datetime.utcnow().year
        next_year = current_year + 1
        current_month_num = datetime.utcnow().month

        # Generate plausible future dates for fallback events
        def get_future_date(month: int, day: int) -> str:
            year_to_use = current_year if month >= current_month_num else next_year
            try:
                 # Construct date object to get month name correctly
                 dt = datetime(year_to_use, month, day)
                 return dt.strftime(f"%B %d, {year_to_use}")
            except ValueError: # Handle invalid day like Feb 30
                 # Fallback to first day of month
                 dt = datetime(year_to_use, month, 1)
                 return dt.strftime(f"%B {day} (approx), {year_to_use}")


        return {
            "eclipses": [
                # KEEP ACTUAL FUTURE ECLIPSES HERE
                {
                    "type": "Partial Lunar Eclipse",
                    "date": "September 18, 2024", # This is past, should be updated
                    "visibility": "Visible from Americas, Europe, Africa, W Asia",
                    "details_link": "https://www.timeanddate.com/eclipse/lunar/2024-september-18",
                    "source": "Fallback Data"
                 },
                 {
                    "type": "Annular Solar Eclipse",
                    "date": "October 2, 2024", # This is past, should be updated
                    "visibility": "Annularity visible from Pacific, S. Chile, S. Argentina. Partial elsewhere in S. South America.",
                    "details_link": "https://www.timeanddate.com/eclipse/solar/2024-october-2",
                    "source": "Fallback Data"
                 },
                 {
                    "type": "Partial Lunar Eclipse",
                    "date": "March 14, 2025",
                    "visibility": "Visible from Americas, Pacific, E Asia, Australia, New Zealand.",
                    "details_link": "https://www.timeanddate.com/eclipse/lunar/2025-march-14",
                    "source": "Fallback Data"
                 },
                {
                    "type": "Partial Solar Eclipse",
                    "date": "March 29, 2025",
                    "visibility": "Visible from NW Africa, Europe, N Russia.",
                    "details_link": "https://www.timeanddate.com/eclipse/solar/2025-march-29",
                    "source": "Fallback Data"
                 },
                 {
                    "type": "Partial Lunar Eclipse",
                    "date": "September 7, 2025",
                    "visibility": "Visible from Europe, Africa, Asia, Australia, W Pacific.",
                    "details_link": "https://www.timeanddate.com/eclipse/lunar/2025-september-7",
                    "source": "Fallback Data"
                 },
                 {
                    "type": "Partial Solar Eclipse",
                    "date": "September 21, 2025",
                    "visibility": "Visible from S Australia, New Zealand, Antarctica.",
                    "details_link": "https://www.timeanddate.com/eclipse/solar/2025-september-21",
                    "source": "Fallback Data"
                 },
                {
                    "type": "Total Lunar Eclipse",
                    "date": "March 3, 2026",
                    "visibility": "Visible from E Asia, Australia, Pacific, Americas.",
                     "details_link": "https://www.timeanddate.com/eclipse/lunar/2026-march-3",
                    "source": "Fallback Data"
                },
                {
                    "type": "Total Solar Eclipse",
                    "date": "August 12, 2026",
                    "visibility": "Totality visible from Arctic, Greenland, Iceland, Spain. Partial elsewhere in Europe, N Africa, N America.",
                    "details_link": "https://www.timeanddate.com/eclipse/solar/2026-august-12",
                    "source": "Fallback Data"
                },

            ],
            "celestial_events": [
                 # Use dynamic dates for fallback events
                {
                    "name": "Perseid Meteor Shower Peak",
                    "date": get_future_date(8, 12), # August 12-13
                    "description": "One of the best meteor showers, producing up to 60 meteors per hour at its peak.",
                    "source": "Fallback Data"
                },
                 {
                    "name": "Saturn at Opposition",
                    "date": get_future_date(9, 8), # September 8
                    "description": "Saturn will be at its closest approach to Earth and its face will be fully illuminated by the Sun.",
                    "source": "Fallback Data"
                },
                {
                    "name": "Neptune at Opposition",
                    "date": get_future_date(9, 21), # September 21
                    "description": "The blue giant planet will be at its closest approach to Earth.",
                    "source": "Fallback Data"
                },
                {
                    "name": "September Equinox",
                    "date": get_future_date(9, 22), # September 22
                    "description": "Marks the first day of autumn in the Northern Hemisphere and spring in the Southern Hemisphere.",
                    "source": "Fallback Data"
                },
                 {
                    "name": "Draconid Meteor Shower",
                    "date": get_future_date(10, 7), # October 7
                    "description": "Minor meteor shower producing only about 10 meteors per hour.",
                    "source": "Fallback Data"
                 },
                 {
                    "name": "Orionid Meteor Shower Peak",
                    "date": get_future_date(10, 21), # October 21-22
                    "description": "Produces up to 20 meteors per hour at its peak.",
                    "source": "Fallback Data"
                 },
                 {
                    "name": "Uranus at Opposition",
                    "date": get_future_date(11, 17), # November 17
                    "description": "The blue-green planet is at its closest approach to Earth.",
                    "source": "Fallback Data"
                 },
                 {
                    "name": "Leonid Meteor Shower Peak",
                    "date": get_future_date(11, 17), # November 17-18
                    "description": "Average shower producing up to 15 meteors per hour, known for periodic spectacular storms.",
                    "source": "Fallback Data"
                 },
                {
                    "name": "Geminid Meteor Shower Peak",
                    "date": get_future_date(12, 14), # December 14-15
                    "description": "Often considered the best meteor shower, potentially producing up to 120 meteors per hour at its peak.",
                    "source": "Fallback Data"
                },
                {
                    "name": "December Solstice",
                    "date": get_future_date(12, 21), # December 21
                    "description": "Marks the first day of winter in the Northern Hemisphere and summer in the Southern Hemisphere.",
                    "source": "Fallback Data"
                },
            ],
             # Fallback moon phases are less useful without complex calculation
             "moon_phases": {
                 "comment": "Fallback moon phases are approximate and may be inaccurate.",
                 "next_full": get_future_date(current_month_num % 12 + 1, 15), # Guess mid-next-month
                 "next_new": get_future_date(current_month_num % 12 + 1, 1), # Guess start of next month
             },
        }


# ---------------------------------------------------------------------------
# Convenience wrapper functions exposed to the LLM runtime
# ---------------------------------------------------------------------------

# Create a single shared instance for caching between calls in the same session
try:
    a_tool
except NameError:
    logger.info("Creating AstronomyTool instance.")
    a_tool = AstronomyTool()


def get_celestial_events(date: Optional[str] = None, location: Optional[str] = None) -> str:
    """
    Fetches and formats information about upcoming celestial events (like meteor showers, conjunctions, equinoxes).

    Args:
        date (Optional[str]): A specific date or month to filter events (e.g., "August 2025", "2025-12-21").
                              If None, fetches general upcoming events. Filtering is approximate.
        location (Optional[str]): Specify a location (e.g., "London", "Tokyo").
                                  Note: General celestial events are often globally observable,
                                  so location filtering might not significantly change the results,
                                  but it's passed for context.

    Returns:
        str: A formatted string listing celestial events, or an error message.
    """
    # Basic input validation/cleaning
    if location and len(location) > 50:
         logger.warning("Location '%s' seems too long, ignoring.", location)
         location = None
    if date and len(date) > 30:
         logger.warning("Date filter '%s' seems too long, ignoring.", date)
         date = None

    logger.info("Tool called: get_celestial_events(date=%s, location=%s)", date, location)
    try:
        data = a_tool.get_celestial_events(date=date, location=location)
        return AstronomyTool.format_celestial_events(data) # Use static method via class
    except Exception as e:
        logger.error("Error in get_celestial_events wrapper: %s", e, exc_info=True)
        return f"An unexpected error occurred in the tool wrapper: {e}"


def get_eclipse_info(location: Optional[str] = None) -> str:
    """
    Fetches and formats information about upcoming solar and lunar eclipses.

    Args:
        location (Optional[str]): Specify a location (e.g., "Barcelona", "New York")
                                  to prioritize eclipses likely visible from that area.
                                  If None, shows a global list.

    Returns:
        str: A formatted string listing upcoming eclipses, potentially filtered by location, or an error message.
    """
     # Basic input validation/cleaning
    if location and len(location) > 50:
         logger.warning("Location '%s' seems too long, ignoring.", location)
         location = None

    logger.info("Tool called: get_eclipse_info(location=%s)", location)
    try:
        data = a_tool.get_eclipse_info(location)
        return AstronomyTool.format_eclipse_info(data) # Use static method via class
    except Exception as e:
        logger.error("Error in get_eclipse_info wrapper: %s", e, exc_info=True)
        return f"An unexpected error occurred in the tool wrapper: {e}"


def get_visible_constellations(location: Optional[str] = None, date: Optional[str] = None) -> str:
    """
    Identifies constellations visible from a location on a given date.

    Args:
        location (Optional[str]): The location from which to check visibility (e.g., "London", "latitude,longitude").
        date (Optional[str]): The specific date (YYYY-MM-DD). If None, defaults to the current date.

    Returns:
        str: A formatted string listing visible constellations and their details.
    """
    logger.info("Tool called: get_visible_constellations(location=%s, date=%s)", location, date)
    try:
        data = a_tool.get_visible_constellations_data(location=location, date=date)
        return AstronomyTool.format_visible_constellations(data)
    except Exception as e:
        logger.error("Error in get_visible_constellations wrapper: %s", e, exc_info=True)
        return f"An unexpected error occurred while getting constellation information: {str(e)}"

def get_planet_info(planet: str) -> str:
    """
    Retrieves details about a specific planet.

    Args:
        planet (str): The name of the planet (e.g., "Mars", "Jupiter").

    Returns:
        str: A formatted string containing detailed information about the planet.
    """
    logger.info("Tool called: get_planet_info(planet=%s)", planet)
    try:
        data = a_tool.get_planet_data(planet)
        return AstronomyTool.format_planet_info(data)
    except Exception as e:
        logger.error("Error in get_planet_info wrapper: %s", e, exc_info=True)
        return f"An unexpected error occurred while getting planet information: {str(e)}"

# ---------------------------------------------------------------------------
# Simple demo when run standalone
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Astronomy Tool Demo — Eclipse Focus\n" + "=" * 40)

    # --- Eclipse Tests ---
    print("\n1. Eclipse Information (Global - Cached):\n")
    print(get_eclipse_info()) # First call - fetches
    time.sleep(1)
    print("\n2. Eclipse Information (Global - Cached):\n")
    print(get_eclipse_info()) # Second call - should use cache

    print("\n" + "-" * 40 + "\n")
    print("3. Eclipse Information for Barcelona (Fetched):\n")
    print(get_eclipse_info("Barcelona"))
    time.sleep(1)
    print("\n4. Eclipse Information for New York (Fetched):\n")
    print(get_eclipse_info("New York"))
    time.sleep(1)
    print("\n5. Eclipse Information for NonExistentPlace (Fetched - fallback filter):\n")
    print(get_eclipse_info("NonExistentPlace"))


    # --- Celestial Event Tests ---
    print("\n" + "=" * 40 + "\n")
    print("6. Celestial Events (Global - Fetched):\n")
    print(get_celestial_events())
    time.sleep(1)
    print("\n7. Celestial Events (Global - Cached):\n")
    print(get_celestial_events())
    time.sleep(1)
    # Test date filtering (exact filtering depends on fetched data format)
    print("\n8. Celestial Events (Filtered by 'August' - Fetched):\n")
    print(get_celestial_events(date="August"))
    time.sleep(1)
    print("\n9. Celestial Events (Filtered by 'December' - Fetched):\n")
    print(get_celestial_events(date="December"))

    print("\n" + "=" * 40 + "\n")
    print("Demo finished.")