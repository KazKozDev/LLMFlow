# tools/wikipedia_tool.py

import requests
import json
import re
import html
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from urllib.parse import quote, urlencode

class WikipediaTool:
    """
    Tool Name: Wikipedia Information Tool
    Description: Retrieves information from Wikipedia articles in multiple languages
    Usage: Can be used to search, get summaries, and extract content from Wikipedia articles
    
    System Prompt Addition:
    ```
    You have access to a Wikipedia Tool that can retrieve information from Wikipedia articles.
    When a user asks about facts, definitions, or information that might be found in an encyclopedia,
    use the wikipedia_tool to get this information.
    
    - To search Wikipedia: Use wikipedia_tool.search_wikipedia("quantum physics")
    - To get a summary: Use wikipedia_tool.get_article_summary("Albert Einstein")
    - To get article content: Use wikipedia_tool.get_article_content("Machine Learning")
    
    This tool doesn't require any API keys and returns verified information from Wikipedia
    with proper attribution.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "wikipedia_tool"
    TOOL_DESCRIPTION = "Retrieve information from Wikipedia articles in multiple languages"
    TOOL_PARAMETERS = [
        {"name": "query", "type": "string", "description": "Search term or article title", "required": True},
        {"name": "language", "type": "string", "description": "Wikipedia language code (default: en)", "required": False},
        {"name": "sections", "type": "string", "description": "Specific sections to retrieve (comma separated)", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What is quantum computing?", "tool_call": "wikipedia_tool.get_article_summary('Quantum computing')"},
        {"query": "Tell me about the history of Rome", "tool_call": "wikipedia_tool.get_article_content('Ancient Rome', sections='History')"},
        {"query": "Who was Marie Curie?", "tool_call": "wikipedia_tool.get_article_summary('Marie Curie')"},
        {"query": "Что такое теория относительности?", "tool_call": "wikipedia_tool.get_article_summary('Теория относительности', language='ru')"}
    ]
    
    def __init__(self):
        """Initialize the WikipediaTool with API endpoints."""
        # Base URLs for different Wikipedia APIs
        self.api_base_url = "https://{lang}.wikipedia.org/w/api.php"
        
        # Default language
        self.default_language = "en"
        
        # Cache for API responses
        self.cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (1 hour)
        self.cache_expiry = 3600
        
        # User agent for API requests
        self.headers = {
            'User-Agent': 'WikipediaToolForLLM/1.0'
        }
        
        # Set initial language and user agent
        self.language = self.default_language
        self.user_agent = self.headers.get('User-Agent')
    
    def search_wikipedia(self, query: str, language: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search Wikipedia for articles matching a query.
        """
        print(f"Searching Wikipedia for: {query}")
        # Validate query
        if not query or not str(query).strip():
            raise Exception("Error searching Wikipedia: query cannot be empty")
        # Determine language
        lang = language if language else self.language
        # Build URL with parameters
        params = {'action': 'query', 'list': 'search', 'srsearch': query, 'format': 'json', 'srlimit': limit}
        url = self.api_base_url.format(lang=lang) + '?' + urlencode(params)
        # Make the request
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
        except Exception as e:
            raise Exception(f"Failed to connect to Wikipedia: {e}")
        # Process response
        try:
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise Exception(f"Error searching Wikipedia: {e}")
        # Extract and slice results list
        raw_results = data.get('query', {}).get('search', [])
        # Respect limit
        sliced = raw_results[:limit] if limit and isinstance(limit, int) and limit > 0 else raw_results
        results = []
        for item in sliced:
            title = item.get('title', '')
            snippet = self._clean_html(item.get('snippet', ''))
            pageid = item.get('pageid', 0)
            results.append({'title': title, 'snippet': snippet, 'pageid': pageid})
        return results
    
    def get_article_summary(self, title: str, language: str = None) -> Dict[str, Any]:
        """
        Get a summary of a Wikipedia article.
        
        Args:
            title (str): Article title or search term
            language (str, optional): Wikipedia language code (default: en)
        
        Returns:
            Dict[str, Any]: Article summary with details
            
        Raises:
            Exception: If the API request fails or article not found
        """
        print(f"Getting Wikipedia summary for: {title}")
        
        # Determine language
        lang = self._determine_language(language, title)
        
        # Check cache
        cache_key = f"summary:{lang}:{title}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached summary for {title}")
            return self.cache[cache_key]
        
        # First try the exact title
        try:
            # Try to get the page directly
            summary_data = self._get_page_extract(title, lang, intro_only=True)
            
            # If successful, cache and return
            self.cache[cache_key] = summary_data
            self.cache_timestamp[cache_key] = current_time
            
            return summary_data
            
        except Exception as direct_error:
            print(f"Direct title lookup failed: {str(direct_error)}")
            
            # If direct lookup fails, try searching
            try:
                search_results = self.search_wikipedia(title, lang, limit=1)
                
                if search_results.get('count', 0) > 0:
                    # Use the first search result
                    first_result = search_results['results'][0]
                    actual_title = first_result['title']
                    
                    print(f"Using search result: {actual_title}")
                    
                    # Get the summary using the found title
                    summary_data = self._get_page_extract(actual_title, lang, intro_only=True)
                    
                    # Cache the result
                    self.cache[cache_key] = summary_data
                    self.cache_timestamp[cache_key] = current_time
                    
                    return summary_data
                else:
                    raise Exception(f"No Wikipedia article found for '{title}'")
                    
            except Exception as search_error:
                error_msg = f"Error getting Wikipedia summary: {str(search_error)}"
                print(error_msg)
                raise Exception(error_msg)
    
    def get_article_content(self, title: str, language: str = None, sections: str = None) -> Dict[str, Any]:
        """
        Get content from a Wikipedia article, optionally filtering by sections.
        
        Args:
            title (str): Article title or search term
            language (str, optional): Wikipedia language code (default: en)
            sections (str, optional): Comma-separated list of sections to include
        
        Returns:
            Dict[str, Any]: Article content with details
            
        Raises:
            Exception: If the API request fails or article not found
        """
        print(f"Getting Wikipedia content for: {title}")
        # If pageid provided as int, fetch by pageids
        if isinstance(title, int):
            pageid = title
            lang = language if language else self.language
            params = {'action': 'query', 'prop': 'extracts', 'pageids': pageid, 'format': 'json', 'explaintext': '1'}
            url = self.api_base_url.format(lang=lang) + '?' + urlencode(params)
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page = pages.get(str(pageid), {})
            if not page or 'missing' in page:
                raise Exception("Article not found")
            extract = page.get('extract', '')
            result = {'title': page.get('title', ''), 'content': extract, 'pageid': pageid}
            # Cache article content
            self._cache_article(pageid, result)
            return result
        
        # Determine language
        lang = self._determine_language(language, title)
        
        # Parse sections
        section_list = None
        if sections:
            section_list = [s.strip() for s in sections.split(',')]
        
        # Check cache
        cache_key = f"content:{lang}:{title}:{sections or 'full'}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached content for {title}")
            return self.cache[cache_key]
        
        # First try the exact title
        try:
            # Try to get the page directly
            content_data = self._get_page_extract(title, lang, intro_only=False)
            
            # Extract and format sections if requested
            if section_list:
                content_data = self._filter_sections(content_data, section_list)
            
            # Cache and return
            self.cache[cache_key] = content_data
            self.cache_timestamp[cache_key] = current_time
            
            return content_data
            
        except Exception as direct_error:
            print(f"Direct title lookup failed: {str(direct_error)}")
            
            # If direct lookup fails, try searching
            try:
                search_results = self.search_wikipedia(title, lang, limit=1)
                
                if search_results.get('count', 0) > 0:
                    # Use the first search result
                    first_result = search_results['results'][0]
                    actual_title = first_result['title']
                    
                    print(f"Using search result: {actual_title}")
                    
                    # Get the content using the found title
                    content_data = self._get_page_extract(actual_title, lang, intro_only=False)
                    
                    # Extract and format sections if requested
                    if section_list:
                        content_data = self._filter_sections(content_data, section_list)
                    
                    # Cache the result
                    self.cache[cache_key] = content_data
                    self.cache_timestamp[cache_key] = current_time
                    
                    return content_data
                else:
                    raise Exception(f"No Wikipedia article found for '{title}'")
                    
            except Exception as search_error:
                error_msg = f"Error getting Wikipedia content: {str(search_error)}"
                print(error_msg)
                raise Exception(error_msg)
    
    def _get_page_extract(self, title: str, language: str, intro_only: bool = False) -> Dict[str, Any]:
        """
        Get the extract (text content) of a Wikipedia page.
        
        Args:
            title (str): Article title
            language (str): Wikipedia language code
            intro_only (bool, optional): Only get the introduction section (default: False)
        
        Returns:
            Dict[str, Any]: Article data with extract
            
        Raises:
            Exception: If the API request fails or article not found
        """
        # Prepare request parameters
        params = {
            'action': 'query',
            'prop': 'extracts|info|categories|images|pageimages|revisions|pageprops',
            'exintro': '1' if intro_only else '0',
            'explaintext': '1',
            'titles': title,
            'format': 'json',
            'inprop': 'url|displaytitle',
            'piprop': 'thumbnail',
            'pithumbsize': 300,
            'rvprop': 'timestamp',
            'rvlimit': 1,
            'redirects': '1',
            'cllimit': 5
        }
        
        # Make the API request
        url = self.api_base_url.format(lang=language)
        response = requests.get(url, params=params, headers=self.headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Process response
        pages = data.get('query', {}).get('pages', {})
        
        # Check if page was found
        if '-1' in pages and 'missing' in pages['-1']:
            raise Exception(f"Wikipedia article '{title}' not found")
        
        # Get the first page (should be only one)
        page_id = next(iter(pages.keys()))
        page = pages[page_id]
        
        # Get page info
        page_title = page.get('title', title)
        page_url = page.get('fullurl', f"https://{language}.wikipedia.org/wiki/{quote(page_title.replace(' ', '_'))}")
        extract = page.get('extract', '')
        
        # Get revision timestamp
        revision = page.get('revisions', [{}])[0]
        timestamp = revision.get('timestamp', datetime.now().isoformat())
        
        # Get thumbnail if available
        thumbnail = None
        if 'thumbnail' in page:
            thumbnail = page['thumbnail'].get('source', None)
        
        # Get categories
        categories = []
        if 'categories' in page:
            categories = [cat.get('title', '').replace('Category:', '') for cat in page.get('categories', [])]
        
        # Get sections
        sections = self._extract_sections(extract)
        
        # Format the result
        result = {
            'title': page_title,
            'pageid': int(page_id),
            'url': page_url,
            'language': language,
            'extract': extract,
            'thumbnail': thumbnail,
            'sections': sections,
            'categories': categories,
            'last_updated': timestamp,
            'timestamp': datetime.now().isoformat(),
            'attribution': f"Content from Wikipedia, retrieved {datetime.now().strftime('%Y-%m-%d')}"
        }
        
        return result
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract section titles and content from Wikipedia text.
        
        Args:
            text (str): Wikipedia article text
            
        Returns:
            List[Dict[str, Any]]: List of sections with titles and content
        """
        # Split the text by newlines
        lines = text.split('\n')
        
        sections = []
        current_section = {'title': 'Introduction', 'level': 0, 'content': ''}
        
        for line in lines:
            # Check if line is a section header (indicated by multiple = signs)
            header_match = re.match(r'^(=+)\s*(.+?)\s*\1$', line)
            
            if header_match:
                # Add the previous section to the list
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # Start a new section
                level = len(header_match.group(1))
                title = header_match.group(2)
                current_section = {
                    'title': title,
                    'level': level,
                    'content': ''
                }
            else:
                # Add line to current section content
                if current_section['content'] and line.strip():
                    current_section['content'] += '\n'
                current_section['content'] += line
        
        # Add the last section
        if current_section['content'].strip():
            sections.append(current_section)
        
        return sections
    
    def _filter_sections(self, article_data: Dict[str, Any], section_names: List[str]) -> Dict[str, Any]:
        """
        Filter article data to include only specified sections.
        
        Args:
            article_data (Dict[str, Any]): Full article data
            section_names (List[str]): List of section titles to include
            
        Returns:
            Dict[str, Any]: Filtered article data
        """
        # Create a copy of the article data
        filtered_data = article_data.copy()
        
        # Get all sections
        all_sections = article_data.get('sections', [])
        
        # Always include Introduction section
        filtered_sections = [s for s in all_sections if s['title'] == 'Introduction']
        
        # Add requested sections (case-insensitive matching)
        section_names_lower = [name.lower() for name in section_names]
        
        for section in all_sections:
            if section['title'].lower() in section_names_lower:
                filtered_sections.append(section)
        
        # Update the extract text to include only selected sections
        filtered_extract = ""
        for section in filtered_sections:
            if section['title'] == 'Introduction':
                filtered_extract += section['content']
            else:
                # Add section header and content
                header = '=' * section['level']
                filtered_extract += f"\n\n{header} {section['title']} {header}\n{section['content']}"
        
        # Update the article data
        filtered_data['extract'] = filtered_extract
        filtered_data['sections'] = filtered_sections
        filtered_data['filtered_sections'] = True
        
        return filtered_data
    
    def _determine_language(self, language: str, text: str) -> str:
        """
        Determine the Wikipedia language to use.
        
        Args:
            language (str): User-specified language code or None
            text (str): Input text to analyze if language is not specified
            
        Returns:
            str: Language code to use
        """
        if language:
            # Use specified language
            return language.lower()
            
        # Detect Russian text
        if re.search(r'[а-яА-Я]', text):
            return 'ru'
            
        # Detect other languages (could be expanded with more language detection)
        # ...
        
        # Default to English
        return self.default_language
    
    def _clean_html(self, text: str) -> str:
        """
        Clean HTML tags and entities from text.
        
        Args:
            text (str): Text with HTML
            
        Returns:
            str: Cleaned text
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_search_description(self, search_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of Wikipedia search results.
        
        Args:
            search_data (Dict[str, Any]): Search data from search_wikipedia
            
        Returns:
            str: Human-readable search results
        """
        query = search_data['query']
        lang = search_data['language']
        count = search_data['count']
        results = search_data['results']
        
        if count == 0:
            return f"No Wikipedia articles found for '{query}' in {lang} Wikipedia."
        
        description = f"Found {count} Wikipedia articles for '{query}':\n\n"
        
        for i, result in enumerate(results):
            title = result['title']
            snippet = result['snippet']
            url = f"https://{lang}.wikipedia.org/wiki/{quote(title.replace(' ', '_'))}"
            
            description += f"{i+1}. {title}\n"
            description += f"   {snippet}\n"
            description += f"   URL: {url}\n\n"
        
        description += f"Source: {lang}.wikipedia.org"
        
        return description
    
    def get_article_description(self, article_data: Dict[str, Any], is_summary: bool = False) -> str:
        """
        Generate a human-readable description of a Wikipedia article.
        
        Args:
            article_data (Dict[str, Any]): Article data from get_article_summary or get_article_content
            is_summary (bool, optional): Whether this is a summary (default: False)
            
        Returns:
            str: Human-readable article content
        """
        title = article_data['title']
        url = article_data['url']
        extract = article_data['extract']
        attribution = article_data['attribution']
        
        if is_summary:
            heading = f"Wikipedia Summary: {title}\n\n"
        else:
            heading = f"Wikipedia Article: {title}\n\n"
        
        # Add the extract
        content = extract
        
        # Add attribution
        footer = f"\n\nSource: {url}\n{attribution}"
        
        return heading + content + footer

    def set_language(self, lang_code: str):
        """Set the language for Wikipedia API requests."""
        import re
        if not isinstance(lang_code, str) or not re.match(r'^[a-z]{2}$', lang_code):
            raise ValueError("Invalid language code")
        self.language = lang_code

    def _get_api_url(self) -> str:
        """Return the formatted API URL for the current language."""
        return self.api_base_url.format(lang=self.language)

    def _cache_article(self, pageid: int, data: Dict[str, Any]) -> None:
        """Cache article content by pageid."""
        key = f"article:{pageid}"
        self.cache[key] = data
        self.cache_timestamp[key] = datetime.now().timestamp()

    def _get_cached_article(self, pageid: int) -> Optional[Dict[str, Any]]:
        """Retrieve cached article content by pageid."""
        key = f"article:{pageid}"
        if key in self.cache and datetime.now().timestamp() - self.cache_timestamp.get(key, 0) < self.cache_expiry:
            return self.cache[key]
        return None

# Functions to expose to the LLM tool system
def search_wikipedia(query, language=None, limit=5):
    """
    Search Wikipedia for articles matching a query.
    
    Args:
        query (str): Search term
        language (str, optional): Wikipedia language code (default: en)
        limit (int, optional): Max number of results (default: 5)
        
    Returns:
        str: Formatted list of search results
    """
    try:
        print(f"search_wikipedia function called with query: {query}, language: {language}, limit: {limit}")
        # Get the tool instance
        tool = WikipediaTool()
        if language:
            tool.set_language(language)
            
        # Perform the search
        results_list = tool.search_wikipedia(query, language=language, limit=int(limit))
        
        # Prepare data for the description formatter
        search_data_dict = {
            "query": query,
            "language": language or tool.language,
            "results": results_list,
            "count": len(results_list)
        }
        
        # Format the description
        description = tool.get_search_description(search_data_dict)
        print(f"Wikipedia search completed with {len(results_list)} results")
        return description
    except Exception as e:
        error_msg = f"Error searching Wikipedia: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_article_summary(title, language=None):
    """
    Get a summary of a Wikipedia article
    
    Args:
        title (str): Article title or search term
        language (str, optional): Wikipedia language code (default: en)
        
    Returns:
        str: Article summary in natural language
    """
    try:
        print(f"get_article_summary function called with title: {title}, language: {language}")
        tool = WikipediaTool()
        article_data = tool.get_article_summary(title, language)
        description = tool.get_article_description(article_data, is_summary=True)
        print(f"Summary retrieved for {article_data['title']}")
        return description
    except Exception as e:
        error_msg = f"Error getting Wikipedia summary: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_article_content(title, language=None, sections=None):
    """
    Get content from a Wikipedia article, optionally filtering by sections
    
    Args:
        title (str): Article title or search term
        language (str, optional): Wikipedia language code (default: en)
        sections (str, optional): Comma-separated list of sections to include
        
    Returns:
        str: Article content in natural language
    """
    try:
        print(f"get_article_content function called with title: {title}, language: {language}, sections: {sections}")
        tool = WikipediaTool()
        article_data = tool.get_article_content(title, language, sections)
        description = tool.get_article_description(article_data)
        print(f"Content retrieved for {article_data['title']}")
        return description
    except Exception as e:
        error_msg = f"Error getting Wikipedia content: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg