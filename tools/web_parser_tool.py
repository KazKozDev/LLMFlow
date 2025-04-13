# tools/web_parser_tool.py

import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse
import re
from readability import Document
from typing import Dict, List, Any, Optional, Union, Tuple

class WebParserTool:
    """
    Tool Name: Web Content Parser Tool
    Description: Extracts and cleans the main content from web pages
    Usage: Can be used to extract readable content from articles, blog posts, and news sites
    
    System Prompt Addition:
    ```
    You have access to a Web Parser Tool that can extract the main content from web pages.
    When a user asks about reading content from a webpage or analyzing a website,
    use the web_parser_tool to get this information.
    
    - To parse a webpage: Use web_parser_tool.parse_webpage("https://example.com/article")
    - To get a summary of a webpage: Use web_parser_tool.get_page_summary("https://example.com/article")
    
    This tool doesn't require any API keys and returns clean, readable text content from web pages
    with proper formatting.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "web_parser_tool"
    TOOL_DESCRIPTION = "Extract and clean the main content from web pages"
    TOOL_PARAMETERS = [
        {"name": "url", "type": "string", "description": "URL of the webpage to parse", "required": True}
    ]
    TOOL_EXAMPLES = [
        {"query": "Extract the content from this article: https://example.com/article", "tool_call": "web_parser_tool.parse_webpage('https://example.com/article')"},
        {"query": "Summarize this webpage: https://example.com/news", "tool_call": "web_parser_tool.get_page_summary('https://example.com/news')"},
        {"query": "What does this blog post say: https://example.com/blog", "tool_call": "web_parser_tool.parse_webpage('https://example.com/blog')"}
    ]
    
    def __init__(self):
        """Initialize the WebParserTool."""
        # User agent for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Cache for parsed content
        self.cache = {}
    
    def is_valid_url(self, url: str) -> bool:
        """
        Check if a URL is valid.
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not url:
            return False
            
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def method1_bs4(self, url: str) -> str:
        """
        Method 1: Parse web content using BeautifulSoup.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Extracted content or error message
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                tag.decompose()
            
            # Search for main content
            article_content = ""
            
            # First look for article tag
            article_tag = soup.find('article')
            if article_tag:
                for p in article_tag.find_all('p'):
                    article_content += p.get_text() + "\n\n"
                if article_content:
                    return article_content.strip()
            
            # Look for divs with classes containing 'content' or 'article'
            content_divs = soup.find_all('div', class_=lambda c: c and ('content' in c.lower() or 'article' in c.lower()))
            for div in content_divs:
                for p in div.find_all('p'):
                    article_content += p.get_text() + "\n\n"
                if article_content:
                    return article_content.strip()
            
            # Just collect all paragraphs
            if not article_content:
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    article_content += p.get_text() + "\n\n"
            
            return article_content.strip()
        except Exception as e:
            return f"Error in method 1: {str(e)}"
    
    def method2_newspaper(self, url: str) -> str:
        """
        Method 2: Parse web content using Newspaper3k.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Extracted content or error message
        """
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if article.text:
                return article.text.strip()
            else:
                return ""
        except Exception as e:
            return f"Error in method 2: {str(e)}"
    
    def method3_readability(self, url: str) -> str:
        """
        Method 3: Parse web content using Readability.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Extracted content or error message
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            doc = Document(response.text)
            content = doc.summary()
            
            # Clean HTML tags
            soup = BeautifulSoup(content, 'html.parser')
            clean_text = soup.get_text()
            
            # Remove extra spaces and line breaks
            clean_text = re.sub(r'\n+', '\n\n', clean_text)
            clean_text = re.sub(r' +', ' ', clean_text)
            
            return clean_text.strip()
        except Exception as e:
            return f"Error in method 3: {str(e)}"
    
    def method4_direct_extraction(self, url: str) -> str:
        """
        Method 4: Direct extraction of text from any elements.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Extracted content or error message
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'aside']):
                tag.decompose()
            
            # Collect text from all elements
            all_text = soup.get_text(separator='\n')
            
            # Clean the text
            clean_text = re.sub(r'\n+', '\n\n', all_text)
            clean_text = re.sub(r' +', ' ', clean_text)
            
            return clean_text.strip()
        except Exception as e:
            return f"Error in method 4: {str(e)}"
    
    def compare_methods(self, url: str) -> str:
        """
        Compare results of different parsing methods and choose the best one.
        
        Args:
            url (str): URL to parse
            
        Returns:
            str: Best extracted content
        """
        method1_result = self.method1_bs4(url)
        method2_result = self.method2_newspaper(url)
        method3_result = self.method3_readability(url)
        method4_result = self.method4_direct_extraction(url)
        
        results = [method1_result, method2_result, method3_result, method4_result]
        best_result = ""
        best_length = 0
        
        for result in results:
            # Skip error results
            if result.startswith("Error") or len(result) < 100:
                continue
                
            if len(result) > best_length:
                best_length = len(result)
                best_result = result
        
        # If all methods returned errors, return the longest result regardless of errors
        if not best_result:
            best_result = max(results, key=len)
        
        return best_result
    
    def clean_text(self, text: str) -> str:
        """
        Additional cleaning of text from unnecessary elements.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        # Remove extra spaces and line breaks
        text = re.sub(r'\n+', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common advertisement and social media elements
        patterns_to_remove = [
            r'Subscribe to.*',
            r'Read also:.*',
            r'Share:.*',
            r'Share.*',
            r'Comments.*',
            r'Copyright ©.*',
            r'\d+ comment(s)?.*',
            r'Advertisement.*',
            r'Loading comments.*',
            r'Popular:.*',
            r'Related:.*',
            r'Source:.*',
        ]
        
        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def parse_webpage(self, url: str) -> Dict[str, Any]:
        """
        Parse a webpage and extract its content.
        
        Args:
            url (str): URL of the webpage to parse
            
        Returns:
            Dict[str, Any]: Parsed content with metadata
            
        Raises:
            Exception: If the URL is invalid or parsing fails
        """
        print(f"Parsing webpage: {url}")
        
        # Check URL validity
        if not self.is_valid_url(url):
            raise Exception(f"Invalid URL: {url}")
        
        # Check cache
        if url in self.cache:
            print(f"Using cached content for {url}")
            return self.cache[url]
        
        # First try with Readability - usually gives the best result
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            doc = Document(response.text)
            content = doc.summary()
            title = doc.title()
            
            # Clean HTML tags
            soup = BeautifulSoup(content, 'html.parser')
            article_text = soup.get_text()
            
            # Clean the text
            clean_article = self.clean_text(article_text)
            
            if clean_article and len(clean_article) > 150:
                # Extract metadata
                meta_soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to get author
                author = None
                author_tags = meta_soup.find_all(['meta'], attrs={'name': re.compile(r'author', re.I)})
                if author_tags:
                    author = author_tags[0].get('content')
                
                # Try to get publication date
                date = None
                date_tags = meta_soup.find_all(['meta'], attrs={'name': re.compile(r'(published|pubdate|date)', re.I)})
                if date_tags:
                    date = date_tags[0].get('content')
                    
                # Try to get description
                description = None
                desc_tags = meta_soup.find_all(['meta'], attrs={'name': re.compile(r'description', re.I)})
                if desc_tags:
                    description = desc_tags[0].get('content')
                
                # Create result
                result = {
                    "url": url,
                    "title": title,
                    "content": clean_article,
                    "metadata": {
                        "author": author,
                        "date": date,
                        "description": description,
                        "word_count": len(clean_article.split()),
                        "char_count": len(clean_article)
                    },
                    "method": "readability"
                }
                
                # Cache the result
                self.cache[url] = result
                
                return result
        except Exception as e:
            print(f"Readability method failed: {str(e)}")
        
        # If Readability failed, try other methods
        best_text = self.compare_methods(url)
        
        if best_text:
            clean_result = self.clean_text(best_text)
            
            # Try to get title
            try:
                response = requests.get(url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.string if soup.title else "Unknown Title"
            except:
                title = "Unknown Title"
            
            # Create result
            result = {
                "url": url,
                "title": title,
                "content": clean_result,
                "metadata": {
                    "word_count": len(clean_result.split()),
                    "char_count": len(clean_result)
                },
                "method": "combined"
            }
            
            # Cache the result
            self.cache[url] = result
            
            return result
        else:
            raise Exception(f"All parsing methods failed for URL: {url}")
    
    def get_page_summary(self, url: str) -> Dict[str, Any]:
        """
        Get a summary of a webpage.
        
        Args:
            url (str): URL of the webpage to summarize
            
        Returns:
            Dict[str, Any]: Page summary with content and metadata
            
        Raises:
            Exception: If the URL is invalid or parsing fails
        """
        print(f"Getting summary for webpage: {url}")
        
        # First parse the webpage
        page_data = self.parse_webpage(url)
        
        # Extract the first few paragraphs (up to 500 characters)
        content = page_data["content"]
        paragraphs = content.split("\n\n")
        
        summary_text = ""
        char_count = 0
        
        for paragraph in paragraphs:
            if char_count + len(paragraph) <= 1000:
                summary_text += paragraph + "\n\n"
                char_count += len(paragraph)
            else:
                # Add part of the paragraph to reach ~1000 characters
                remaining = 1000 - char_count
                if remaining > 50:  # Only add if we can include a meaningful chunk
                    summary_text += paragraph[:remaining] + "..."
                break
        
        # Create summary result
        result = {
            "url": url,
            "title": page_data["title"],
            "summary": summary_text.strip(),
            "metadata": page_data["metadata"],
            "full_content_available": True
        }
        
        return result
    
    def get_webpage_description(self, webpage_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of a parsed webpage.
        
        Args:
            webpage_data (Dict[str, Any]): Parsed webpage data
            
        Returns:
            str: Human-readable webpage description
        """
        url = webpage_data["url"]
        title = webpage_data["title"]
        content = webpage_data.get("content", webpage_data.get("summary", ""))
        
        metadata = webpage_data.get("metadata", {})
        author = metadata.get("author", "Unknown Author")
        date = metadata.get("date", "Unknown Date")
        word_count = metadata.get("word_count", len(content.split()))
        
        if author and author != "Unknown Author":
            author_text = f"by {author}"
        else:
            author_text = ""
        
        if date and date != "Unknown Date":
            date_text = f"published on {date}"
        else:
            date_text = ""
        
        metadata_text = f"{author_text} {date_text}".strip()
        if metadata_text:
            metadata_text = f" ({metadata_text})"
        
        description = f"Content from: {title}{metadata_text}\nSource: {url}\nWord count: {word_count}\n\n{content}"
        
        return description

# Functions to expose to the LLM tool system
def parse_webpage(url):
    """
    Parse a webpage and extract its main content
    
    Args:
        url (str): URL of the webpage to parse
        
    Returns:
        str: Extracted content in natural language
    """
    try:
        print(f"parse_webpage function called with URL: {url}")
        tool = WebParserTool()
        webpage_data = tool.parse_webpage(url)
        description = tool.get_webpage_description(webpage_data)
        print(f"Webpage parsed successfully")
        return description
    except Exception as e:
        error_msg = f"Error parsing webpage: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_page_summary(url):
    """
    Get a summary of a webpage
    
    Args:
        url (str): URL of the webpage to summarize
        
    Returns:
        str: Webpage summary in natural language
    """
    try:
        print(f"get_page_summary function called with URL: {url}")
        tool = WebParserTool()
        summary_data = tool.get_page_summary(url)
        description = tool.get_webpage_description(summary_data)
        print(f"Webpage summary generated")
        return description
    except Exception as e:
        error_msg = f"Error getting webpage summary: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg