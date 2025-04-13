# tools/search_tool.py

import requests
from bs4 import BeautifulSoup
import random
import time
import hashlib
import os
from datetime import datetime, timedelta
import logging
import urllib.parse
import json
from typing import List, Dict, Union, Optional, Tuple, Any  # Added Any to the imports

class SearchTool:
    """
    Tool Name: Web Search Tool
    Description: Performs web searches using DuckDuckGo without being blocked
    Usage: Can be used to find information on any topic through web search
    
    System Prompt Addition:
    ```
    You have access to a Web Search Tool that can search the internet for information.
    When a user asks for information that you don't know or that may be more recent than your knowledge,
    use the search_tool to find up-to-date information.
    
    - To search for information: Use search_tool.search_web("query here")
    - To get a specific number of results: Use search_tool.search_web("query here", 5)
    
    This tool doesn't require any API keys and returns real search results from the web
    with proper attribution.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "search_tool"
    TOOL_DESCRIPTION = "Search the web for information on any topic using DuckDuckGo"
    TOOL_PARAMETERS = [
        {"name": "query", "type": "string", "description": "Search query", "required": True},
        {"name": "num_results", "type": "integer", "description": "Number of results to return (default: 10)", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What are the latest developments in AI?", "tool_call": "search_tool.search_web('latest developments in artificial intelligence')"},
        {"query": "Find information about climate change", "tool_call": "search_tool.search_web('climate change impacts and solutions')"},
        {"query": "Who won the last World Cup?", "tool_call": "search_tool.search_web('who won the last FIFA World Cup')"},
        {"query": "Search for news about quantum computing", "tool_call": "search_tool.search_web('quantum computing recent breakthroughs', 5)"}
    ]
    
    def __init__(self):
        """Initialize the SearchTool."""
        # Configure logging
        self.logger = logging.getLogger("search_tool")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:96.0) Gecko/20100101 Firefox/96.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/97.0.1072.55",
            "Mozilla/5.0 (iPad; CPU OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1"
        ]
        
        # Cache settings
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search_cache")
        self.cache_expiration = timedelta(hours=24)  # Cache results for 24 hours
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_random_user_agent(self) -> str:
        """Return a random User-Agent from the list of popular browsers."""
        return random.choice(self.user_agents)
    
    def get_cache_path(self, query: str) -> str:
        """
        Get the cache file path for a query.
        
        Args:
            query (str): The search query
            
        Returns:
            str: Path to the cache file
        """
        # Create a hash of the query to use as the filename
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{query_hash}.json")
    
    def get_cached_results(self, query: str) -> Optional[List[Dict]]:
        """
        Get cached results for a query if they exist and are not expired.
        
        Args:
            query (str): The search query
            
        Returns:
            list or None: The cached results or None if not found or expired
        """
        cache_path = self.get_cache_path(query)
        
        if not os.path.exists(cache_path):
            return None
            
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # Check if the cache is expired
            cached_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cached_time > self.cache_expiration:
                self.logger.debug(f"Cache for '{query}' has expired.")
                return None
                
            self.logger.info(f"Using cached results for '{query}'")
            return cached_data['results']
        except Exception as e:
            self.logger.warning(f"Error reading cache: {e}")
            return None
    
    def save_to_cache(self, query: str, results: List[Dict]) -> None:
        """
        Save search results to cache.
        
        Args:
            query (str): The search query
            results (list): The search results to cache
        """
        if not results:
            return
            
        cache_path = self.get_cache_path(query)
        
        try:
            cache_data = {
                'query': query,
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Results for '{query}' saved to cache")
        except Exception as e:
            self.logger.warning(f"Error saving to cache: {e}")
    
    def search_web(self, query: str, num_results: int = 10) -> Dict[str, Any]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query (str): The search query
            num_results (int, optional): Number of results to return (default: 10)
            
        Returns:
            Dict[str, Any]: Search results with metadata
            
        Raises:
            Exception: If the search fails
        """
        self.logger.info(f"Searching for: {query}")
        
        # Check cache first
        cached_results = self.get_cached_results(query)
        if cached_results is not None:
            # Limit results to requested number
            limited_results = cached_results[:num_results] if num_results > 0 else cached_results
            
            return {
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "results": limited_results,
                "source": "cache"
            }
        
        # Try to search with HTML version first
        results = self._search_html_version(query)
        
        # If HTML version fails, try lite version
        if not results:
            self.logger.info("HTML version failed, trying lite version")
            results = self._search_lite_version(query)
        
        # If we got results, cache them
        if results:
            self.save_to_cache(query, results)
        else:
            raise Exception(f"No search results found for: {query}")
        
        # Limit results to requested number
        limited_results = results[:num_results] if num_results > 0 else results
        
        # Return formatted results
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results": limited_results,
            "source": "DuckDuckGo",
            "result_count": len(limited_results)
        }
    
    def _search_html_version(self, query: str) -> List[Dict]:
        """
        Search using the HTML version of DuckDuckGo.
        
        Args:
            query (str): The search query
            
        Returns:
            list: The search results
        """
        encoded_query = urllib.parse.quote(query)
        url = f"https://duckduckgo.com/html/?q={encoded_query}"
        
        # Add some random parameters to look more like a browser
        params = []
        possible_params = [
            ("kl", random.choice(["ru-ru", "us-en", "wt-wt"])),  # Locale
            ("k1", "-1"),  # Disable safe search
            ("kp", str(random.choice([-2, -1, 0, 1, 2]))),  # Filter level
            ("kaf", str(random.randint(0, 1))),  # Auto-correction
            ("kd", str(random.randint(0, 1))),  # Suggestions
        ]
        
        selected_params = random.sample(possible_params, k=random.randint(1, len(possible_params)))
        params = [f"{k}={v}" for k, v in selected_params]
        
        if params:
            url = f"{url}&{'&'.join(params)}"
            
        response = self._make_request(url)
        if not response:
            return []
            
        return self._extract_html_results(response.text)
    
    def _search_lite_version(self, query: str) -> List[Dict]:
        """
        Search using the lite version of DuckDuckGo.
        
        Args:
            query (str): The search query
            
        Returns:
            list: The search results
        """
        encoded_query = urllib.parse.quote(query)
        url = f"https://lite.duckduckgo.com/lite/?q={encoded_query}"
        
        response = self._make_request(url)
        if not response:
            return []
            
        return self._extract_lite_results(response.text)
    
    def _make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """
        Make an HTTP request with retries and exponential backoff.
        
        Args:
            url (str): The URL to request
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Response or None: The response object or None if the request failed
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Add a random delay to mimic human behavior
                time.sleep(random.uniform(1.0, 3.0))
                
                # Get a random user agent and set up headers
                user_agent = self.get_random_user_agent()
                headers = {
                    "User-Agent": user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Referer": "https://duckduckgo.com/",
                    "DNT": "1",  # Do Not Track
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1"
                }
                
                # Make the request
                response = requests.get(
                    url,
                    headers=headers,
                    cookies={"ax": str(random.randint(1, 9))},
                    timeout=15
                )
                
                # Check for success
                if response.status_code == 200:
                    # Check for CAPTCHA or blocking
                    if any(term in response.text.lower() for term in ["captcha", "blocked", "too many requests"]):
                        self.logger.warning("CAPTCHA or blocking detected. Retrying...")
                        retry_count += 1
                        time.sleep(2 ** retry_count + random.uniform(1, 3))
                        continue
                        
                    return response
                    
                elif response.status_code == 429 or response.status_code >= 500:
                    # Too many requests or server error
                    self.logger.warning(f"Got status code {response.status_code}. Retrying...")
                    retry_count += 1
                    time.sleep(2 ** retry_count + random.uniform(1, 3))
                else:
                    self.logger.error(f"Error: Got status code {response.status_code}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request error: {e}")
                retry_count += 1
                time.sleep(2 ** retry_count + random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return None
                
        self.logger.error(f"Failed to make request after {max_retries} retries")
        return None
    
    def _extract_html_results(self, html_content: str) -> List[Dict]:
        """
        Extract search results from the HTML version of DuckDuckGo.
        
        Args:
            html_content (str): The HTML content
            
        Returns:
            list: The extracted search results
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # Try multiple selector patterns to find results
            selectors_to_try = [
                "div.result", "div.results_links", "div.results_links_deep", 
                "div.web-result", "article.result", "article.result__web",
                "div.PartialWebResult", "div.PartialWebResult-title",
                "div[data-testid='result']", "div[data-testid='web-result']"
            ]
            
            result_elements = []
            for selector in selectors_to_try:
                result_elements = soup.select(selector)
                if result_elements:
                    self.logger.debug(f"Found {len(result_elements)} results using selector: {selector}")
                    break
            
            # If no results found through selectors, try alternative method
            if not result_elements or len(result_elements) < 3:
                self.logger.debug("Standard selectors didn't find enough results, trying alternative method")
                result_elements = self._find_results_alternative(soup)
            
            # Process found elements
            for result in result_elements:
                try:
                    # Find title and link
                    title_selectors = ["a.result__a", "a.result__url", "a[data-testid='result-title-a']",
                                      "a.title", "h2 a", "h3 a", ".result__title a", ".PartialWebResult-title a"]
                    
                    title_element = None
                    for selector in title_selectors:
                        title_element = result.select_one(selector)
                        if title_element:
                            break
                    
                    if not title_element:
                        # If we couldn't find with selectors, just look for any link
                        title_element = result.find('a')
                    
                    if not title_element:
                        continue
                        
                    title = title_element.get_text().strip()
                    link = title_element.get("href", "")
                    
                    # Skip internal links or empty links
                    if not link or link.startswith("javascript:") or link == "#":
                        continue
                        
                    # Handle DuckDuckGo redirect URLs
                    if "/y.js?" in link or "/l.js?" in link or "uddg=" in link:
                        parsed_url = urllib.parse.urlparse(link)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        
                        if 'uddg' in query_params:
                            link = urllib.parse.unquote(query_params['uddg'][0])
                        elif 'u' in query_params:
                            link = urllib.parse.unquote(query_params['u'][0])
                        else:
                            continue
                    
                    # Find description
                    desc_selectors = ["a.result__snippet", "div.result__snippet", ".snippet", 
                                     ".snippet__content", "div[data-testid='result-snippet']",
                                     ".PartialWebResult-snippet", ".result__body"]
                    
                    desc_element = None
                    for selector in desc_selectors:
                        desc_element = result.select_one(selector)
                        if desc_element:
                            break
                    
                    description = ""
                    if desc_element:
                        description = desc_element.get_text().strip()
                    
                    # If no description found but we have a title and link, still add the result
                    if title and link:
                        results.append({
                            "title": title,
                            "link": link,
                            "description": description
                        })
                except Exception as e:
                    self.logger.debug(f"Error processing result element: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error extracting HTML results: {e}")
        
        return results
    
    def _extract_lite_results(self, html_content: str) -> List[Dict]:
        """
        Extract search results from the lite version of DuckDuckGo.
        
        Args:
            html_content (str): The HTML content
            
        Returns:
            list: The extracted search results
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            
            # The lite version uses a simple table layout
            # Look for table rows with links
            result_rows = soup.select('table tr:has(a)')
            
            # If we didn't find results with the selector, try a more general approach
            if not result_rows:
                self.logger.debug("Standard lite selectors didn't work, trying alternative approach")
                result_rows = []
                for table in soup.find_all('table'):
                    for row in table.find_all('tr'):
                        if row.find('a'):
                            result_rows.append(row)
            
            for row in result_rows:
                try:
                    # Find the link element
                    link_elem = row.find('a')
                    if not link_elem:
                        continue
                    
                    title = link_elem.get_text().strip()
                    link = link_elem.get('href', '')
                    
                    # Skip empty links or internal links
                    if not link or link.startswith('/'):
                        continue
                    
                    # In the lite version, the description is often in the next row
                    description = ""
                    next_row = row.find_next_sibling('tr')
                    if next_row:
                        # Description is usually in the first cell without a link
                        desc_cells = [cell for cell in next_row.find_all('td') if not cell.find('a')]
                        if desc_cells:
                            description = desc_cells[0].get_text().strip()
                    
                    # Add to results
                    if title and link:
                        results.append({
                            "title": title,
                            "link": link,
                            "description": description
                        })
                except Exception as e:
                    self.logger.debug(f"Error processing lite result row: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Error extracting lite results: {e}")
        
        return results
    
    def _find_results_alternative(self, soup: BeautifulSoup) -> List:
        """
        Alternative method to find search results when standard selectors fail.
        
        Args:
            soup (BeautifulSoup): The parsed HTML
            
        Returns:
            list: Found result elements
        """
        results = []
        
        # Strategy 1: Look for heading links
        heading_links = soup.select('h2 a, h3 a, h4 a')
        if heading_links:
            self.logger.debug(f"Found {len(heading_links)} potential results using heading links")
            # For each heading link, find its containing block (likely a result container)
            for link in heading_links:
                # Go up several levels to find potential container
                container = link
                for _ in range(3):  # Try going up to 3 levels
                    if container.parent:
                        container = container.parent
                    else:
                        break
                
                # Only add containers we haven't seen yet
                if container not in results:
                    results.append(container)
        
        # Strategy 2: Look for link clusters
        if len(results) < 5:  # If we didn't find enough results
            self.logger.debug("Looking for link clusters as fallback")
            links = soup.find_all('a')
            
            # Group links by their parent
            link_parents = {}
            for link in links:
                parent = link.parent
                if parent:
                    if parent not in link_parents:
                        link_parents[parent] = []
                    link_parents[parent].append(link)
            
            # Find parents with exactly one link (potential results)
            for parent, parent_links in link_parents.items():
                if len(parent_links) == 1 and parent not in results:
                    # Go up one level to get the container
                    container = parent.parent if parent.parent else parent
                    if container not in results:
                        results.append(container)
        
        return results
    
    def get_search_results_description(self, search_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of search results.
        
        Args:
            search_data (Dict[str, Any]): Search results data
            
        Returns:
            str: Human-readable search results description
        """
        query = search_data["query"]
        results = search_data["results"]
        result_count = len(results)
        
        if result_count == 0:
            return f"No search results found for '{query}'."
        
        # Create a header
        description = f"Search results for '{query}' ({result_count} results):\n\n"
        
        # Add each result
        for i, result in enumerate(results, 1):
            title = result["title"]
            link = result["link"]
            snippet = result["description"]
            
            description += f"{i}. {title}\n"
            description += f"   {link}\n"
            if snippet:
                description += f"   {snippet}\n"
            description += "\n"
        
        # Add attribution
        description += f"Source: DuckDuckGo search results"
        
        return description

# Functions to expose to the LLM tool system
def search_web(query, num_results=10):
    """
    Search the web for information on a topic
    
    Args:
        query (str): Search query
        num_results (int, optional): Number of results to return (default: 10)
        
    Returns:
        str: Search results in natural language
    """
    try:
        print(f"search_web function called with query: {query}, num_results: {num_results}")
        tool = SearchTool()
        search_data = tool.search_web(query, int(num_results))
        description = tool.get_search_results_description(search_data)
        print(f"Search completed with {len(search_data['results'])} results")
        return description
    except Exception as e:
        error_msg = f"Error searching the web: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg