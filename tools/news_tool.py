# tools/news_tool.py

import requests
import json
import feedparser
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
import re
import html
from urllib.parse import quote

class NewsTool:
    """
    Tool Name: News Information Tool
    Description: Retrieves latest news from multiple sources using RSS feeds
    Usage: Can be used to get news by topic/keyword or browse latest headlines by category
    
    System Prompt Addition:
    ```
    You have access to a News Tool that can retrieve the latest news articles from reliable sources.
    When a user asks about recent news, specific topics, or current events, use the news_tool to get this information.
    
    - To search for news by topic: Use news_tool.search_news("bitcoin") or news_tool.search_news("climate change")
    - To get latest headlines by category: Use news_tool.get_headlines("business") or news_tool.get_headlines("technology")
    
    This tool doesn't require any API keys and returns recent news articles including titles, 
    descriptions, sources, and publication dates.
    ```
    """
    
    # Tool metadata
    TOOL_NAME = "news_tool"
    TOOL_DESCRIPTION = "Get the latest news on any topic or browse headlines by category"
    TOOL_PARAMETERS = [
        {"name": "query", "type": "string", "description": "News topic, keyword, or category", "required": True},
        {"name": "max_results", "type": "integer", "description": "Maximum number of results to return (default: 5)", "required": False}
    ]
    TOOL_EXAMPLES = [
        {"query": "What's the latest news on climate change?", "tool_call": "news_tool.search_news('climate change')"},
        {"query": "Show me recent technology news", "tool_call": "news_tool.get_headlines('technology')"},
        {"query": "Any news about SpaceX?", "tool_call": "news_tool.search_news('SpaceX')"},
        {"query": "последние новости о России", "tool_call": "news_tool.search_news('Россия')"}
    ]
    
    def __init__(self):
        """Initialize the NewsTool with RSS feed sources."""
        # News categories and their corresponding RSS feeds
        self.news_feeds = {
            "general": [
                "http://rss.cnn.com/rss/cnn_topstories.rss",
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
                "https://news.google.com/rss",
                "https://www.huffpost.com/section/front-page/feed"
            ],
            "world": [
                "https://feeds.bbci.co.uk/news/world/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
                "http://rss.cnn.com/rss/cnn_world.rss"
            ],
            "business": [
                "https://feeds.bbci.co.uk/news/business/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
                "http://rss.cnn.com/rss/money_latest.rss",
                "https://www.wsj.com/xml/rss/3_7031.xml"
            ],
            "technology": [
                "https://feeds.bbci.co.uk/news/technology/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
                "https://www.wired.com/feed/rss",
                "https://techcrunch.com/feed/"
            ],
            "science": [
                "https://rss.nytimes.com/services/xml/rss/nyt/Science.xml",
                "https://www.sciencedaily.com/rss/all.xml",
                "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
            ],
            "health": [
                "https://feeds.bbci.co.uk/news/health/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml",
                "https://www.who.int/rss-feeds/news-english.xml"
            ],
            "sports": [
                "https://feeds.bbci.co.uk/sport/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml",
                "http://rss.cnn.com/rss/edition_sport.rss",
                "https://www.espn.com/espn/rss/news"
            ],
            "entertainment": [
                "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Arts.xml",
                "https://variety.com/feed/"
            ],
            "politics": [
                "https://feeds.bbci.co.uk/news/politics/rss.xml",
                "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
                "http://rss.cnn.com/rss/cnn_allpolitics.rss"
            ]
        }
        
        # Search-optimized feeds that work well with query parameters
        self.search_feeds = [
            "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q={query}&hl=en-GB&gl=GB&ceid=GB:en"
        ]
        
        # Russian-language feeds for multilingual support
        self.russian_feeds = {
            "general": [
                "https://lenta.ru/rss",
                "https://tass.ru/rss/v2.xml",
                "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru"
            ]
        }
        
        # Cache for news results to minimize RSS fetching
        self.news_cache = {}
        self.cache_timestamp = {}
        # Cache expiry in seconds (15 minutes)
        self.cache_expiry = 900
    
    def search_news(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search for news articles on a specific topic or keyword.
        
        Args:
            query (str): The news topic or keyword to search for
            max_results (int, optional): Maximum number of results to return (default: 5)
        
        Returns:
            Dict[str, Any]: News search results with details
            
        Raises:
            Exception: If RSS fetching fails
        """
        print(f"Searching news for query: {query}")
        
        # Check if query is in Russian
        is_russian = bool(re.search('[а-яА-Я]', query))
        
        # Use cached results if available and fresh
        cache_key = f"search:{query}:{max_results}:{is_russian}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.news_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached news results for {query}")
            return self.news_cache[cache_key]
        
        # Prepare feeds to search
        if is_russian:
            print("Detected Russian query, using Russian news sources")
            feeds_to_search = self.russian_feeds["general"]
        else:
            # Format the search feeds with the query
            feeds_to_search = [feed.format(query=quote(query)) for feed in self.search_feeds]
            # Also add some general feeds
            feeds_to_search.extend(self.news_feeds["general"])
        
        # Collect all news articles
        all_articles = []
        
        # Fetch and parse each feed
        for feed_url in feeds_to_search:
            try:
                print(f"Fetching feed: {feed_url}")
                feed_data = feedparser.parse(feed_url)
                
                if feed_data.entries:
                    # Extract articles from this feed
                    articles = self._extract_articles(feed_data, query)
                    all_articles.extend(articles)
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}")
                # Continue with other feeds if one fails
                continue
        
        # Sort by relevance and publication date
        all_articles = self._rank_articles(all_articles, query)
        
        # Limit the number of results
        limited_articles = all_articles[:max_results]
        
        # Format the results
        result = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "count": len(limited_articles),
            "articles": limited_articles
        }
        
        # Cache the results
        self.news_cache[cache_key] = result
        self.cache_timestamp[cache_key] = current_time
        
        return result
    
    def get_headlines(self, category: str = "general", max_results: int = 5) -> Dict[str, Any]:
        """
        Get the latest news headlines by category.
        
        Args:
            category (str, optional): News category (default: "general")
            max_results (int, optional): Maximum number of results to return (default: 5)
        
        Returns:
            Dict[str, Any]: Latest headlines with details
            
        Raises:
            Exception: If RSS fetching fails or category is invalid
        """
        print(f"Getting headlines for category: {category}")
        
        # Normalize category name
        category = category.lower().strip()
        
        # Map common category variations
        category_mapping = {
            "business": "business",
            "finance": "business",
            "economy": "business",
            "money": "business",
            "tech": "technology",
            "technology": "technology",
            "science": "science",
            "research": "science",
            "health": "health",
            "medical": "health",
            "medicine": "health",
            "sports": "sports",
            "sport": "sports",
            "entertainment": "entertainment",
            "arts": "entertainment",
            "culture": "entertainment",
            "movies": "entertainment",
            "politics": "politics",
            "political": "politics",
            "world": "world",
            "international": "world",
            "global": "world",
            "top": "general",
            "main": "general",
            "breaking": "general",
            "latest": "general",
            "recent": "general"
        }
        
        # Map the category to our standard categories
        if category in category_mapping:
            mapped_category = category_mapping[category]
        else:
            # Default to general if category not recognized
            mapped_category = "general"
        
        # Use cached results if available and fresh
        cache_key = f"headlines:{mapped_category}:{max_results}"
        current_time = datetime.now().timestamp()
        if (cache_key in self.news_cache and 
            current_time - self.cache_timestamp.get(cache_key, 0) < self.cache_expiry):
            print(f"Using cached headlines for {mapped_category}")
            return self.news_cache[cache_key]
        
        # Get the feeds for this category
        if mapped_category in self.news_feeds:
            feeds = self.news_feeds[mapped_category]
        else:
            raise Exception(f"Category '{category}' not supported")
        
        # Collect all news articles
        all_articles = []
        
        # Fetch and parse each feed
        for feed_url in feeds:
            try:
                print(f"Fetching feed: {feed_url}")
                feed_data = feedparser.parse(feed_url)
                
                if feed_data.entries:
                    # Extract articles from this feed
                    articles = self._extract_articles(feed_data)
                    all_articles.extend(articles)
            except Exception as e:
                print(f"Error fetching feed {feed_url}: {e}")
                # Continue with other feeds if one fails
                continue
        
        # Sort by publication date (newest first)
        all_articles = sorted(
            all_articles, 
            key=lambda x: datetime.fromisoformat(x.get("published_date", "2000-01-01T00:00:00")), 
            reverse=True
        )
        
        # Remove duplicates (based on title similarity)
        unique_articles = self._remove_duplicates(all_articles)
        
        # Limit the number of results
        limited_articles = unique_articles[:max_results]
        
        # Format the results
        result = {
            "category": mapped_category,
            "original_query": category,
            "timestamp": datetime.now().isoformat(),
            "count": len(limited_articles),
            "articles": limited_articles
        }
        
        # Cache the results
        self.news_cache[cache_key] = result
        self.cache_timestamp[cache_key] = current_time
        
        return result
    
    def _extract_articles(self, feed_data: Any, query: str = None) -> List[Dict[str, Any]]:
        """
        Extract articles from a parsed RSS feed.
        
        Args:
            feed_data (Any): Parsed RSS feed from feedparser
            query (str, optional): Search query for filtering results
            
        Returns:
            List[Dict[str, Any]]: List of extracted articles
        """
        articles = []
        
        for entry in feed_data.entries:
            try:
                # Extract the title and clean it
                title = entry.get("title", "No title")
                title = self._clean_text(title)
                
                # Skip if empty title or title is too short
                if not title or len(title) < 5:
                    continue
                
                # Extract description/summary
                description = ""
                if "summary" in entry:
                    description = self._clean_text(entry.summary)
                elif "description" in entry:
                    description = self._clean_text(entry.description)
                
                # Extract source
                source = ""
                if "source" in entry and hasattr(entry.source, "title"):
                    source = entry.source.title
                elif hasattr(feed_data, "feed") and hasattr(feed_data.feed, "title"):
                    source = feed_data.feed.title
                
                # Clean the source
                source = self._clean_text(source)
                if not source:
                    source = "Unknown Source"
                
                # Extract link
                link = entry.get("link", "")
                
                # Extract publication date
                published_date = self._extract_date(entry)
                
                # Create article object
                article = {
                    "title": title,
                    "description": description,
                    "source": source,
                    "link": link,
                    "published_date": published_date,
                    "relevance_score": 0  # Will be set later for search results
                }
                
                # If we have a query, calculate relevance score
                if query:
                    article["relevance_score"] = self._calculate_relevance(article, query)
                
                articles.append(article)
                
            except Exception as e:
                print(f"Error extracting article: {e}")
                # Skip this article if there was an error
                continue
        
        return articles
    
    def _extract_date(self, entry: Any) -> str:
        """
        Extract and standardize publication date from a feed entry.
        
        Args:
            entry (Any): RSS feed entry
            
        Returns:
            str: ISO format date string
        """
        # Check various date fields
        if "published_parsed" in entry and entry.published_parsed:
            try:
                return time.strftime("%Y-%m-%dT%H:%M:%S", entry.published_parsed)
            except:
                pass
                
        if "updated_parsed" in entry and entry.updated_parsed:
            try:
                return time.strftime("%Y-%m-%dT%H:%M:%S", entry.updated_parsed)
            except:
                pass
        
        if "published" in entry:
            try:
                date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
                return date.isoformat()
            except:
                pass
        
        if "updated" in entry:
            try:
                date = datetime.strptime(entry.updated, "%a, %d %b %Y %H:%M:%S %z")
                return date.isoformat()
            except:
                pass
        
        # Default to current time if we can't parse the date
        return datetime.now().isoformat()
    
    def _clean_text(self, text: str) -> str:
        """
        Clean text by removing HTML tags, entities, and extra whitespace.
        
        Args:
            text (str): Text to clean
            
        Returns:
            str: Cleaned text
        """
        if not text:
            return ""
            
        # Convert HTML entities
        text = html.unescape(text)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _calculate_relevance(self, article: Dict[str, Any], query: str) -> float:
        """
        Calculate relevance score of an article to the search query.
        
        Args:
            article (Dict[str, Any]): Article data
            query (str): Search query
            
        Returns:
            float: Relevance score (0-10)
        """
        # Prepare the query and article text for comparison
        query_lower = query.lower()
        title_lower = article["title"].lower()
        desc_lower = article["description"].lower()
        
        # Basic relevance calculation
        relevance = 0
        
        # Title matches are most important
        if query_lower in title_lower:
            relevance += 5
            # Exact title match or starts with query
            if title_lower == query_lower or title_lower.startswith(query_lower):
                relevance += 3
        
        # Description matches
        if query_lower in desc_lower:
            relevance += 2
        
        # Check for partial word matches in title
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 3 and word in title_lower:
                relevance += 1
            if len(word) > 3 and word in desc_lower:
                relevance += 0.5
        
        # Freshness bonus (newer articles get higher score)
        try:
            pub_date = datetime.fromisoformat(article["published_date"])
            now = datetime.now()
            age_hours = (now - pub_date).total_seconds() / 3600
            
            # Articles less than 24 hours old get a bonus
            if age_hours < 24:
                freshness_bonus = (24 - age_hours) / 24  # Range from 0 to 1
                relevance += freshness_bonus
        except Exception as e:
            print(f"Error calculating freshness: {e}")
        
        # Cap the relevance score at 10
        return min(10, relevance)
    
    def _rank_articles(self, articles: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """
        Rank articles by relevance and freshness.
        
        Args:
            articles (List[Dict[str, Any]]): List of articles
            query (str): Search query
            
        Returns:
            List[Dict[str, Any]]: Ranked list of articles
        """
        # Calculate relevance scores if not already done
        for article in articles:
            if article["relevance_score"] == 0:
                article["relevance_score"] = self._calculate_relevance(article, query)
        
        # Sort by relevance score (highest first)
        sorted_articles = sorted(articles, key=lambda x: x["relevance_score"], reverse=True)
        
        # Remove duplicates
        unique_articles = self._remove_duplicates(sorted_articles)
        
        return unique_articles
    
    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate or very similar articles.
        
        Args:
            articles (List[Dict[str, Any]]): List of articles
            
        Returns:
            List[Dict[str, Any]]: List with duplicates removed
        """
        unique_articles = []
        titles_seen = set()
        
        for article in articles:
            # Create a simplified version of the title for comparison
            simple_title = re.sub(r'[^\w\s]', '', article["title"].lower())
            
            # Skip if we've seen a very similar title
            if simple_title in titles_seen:
                continue
            
            # Check for high similarity with existing titles
            duplicate = False
            for seen_title in titles_seen:
                if self._similar_titles(simple_title, seen_title):
                    duplicate = True
                    break
            
            if not duplicate:
                titles_seen.add(simple_title)
                unique_articles.append(article)
        
        return unique_articles
    
    def _similar_titles(self, title1: str, title2: str) -> bool:
        """
        Check if two titles are very similar.
        
        Args:
            title1 (str): First title
            title2 (str): Second title
            
        Returns:
            bool: True if titles are similar, False otherwise
        """
        # If one title is contained within the other
        if title1 in title2 or title2 in title1:
            return True
            
        # If the titles are very close in length and share most words
        words1 = set(title1.split())
        words2 = set(title2.split())
        
        if len(words1) == 0 or len(words2) == 0:
            return False
            
        common_words = words1.intersection(words2)
        similarity = len(common_words) / min(len(words1), len(words2))
        
        return similarity > 0.8
    
    def get_news_description(self, news_data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the news results.
        
        Args:
            news_data (Dict[str, Any]): News data from search_news or get_headlines
            
        Returns:
            str: Human-readable news description
        """
        articles = news_data.get("articles", [])
        count = len(articles)
        
        if "query" in news_data:
            # This is search results
            query = news_data["query"]
            header = f"Here are {count} news results for '{query}':\n\n"
        else:
            # This is headlines by category
            category = news_data.get("category", "general").capitalize()
            header = f"Here are {count} latest {category} headlines:\n\n"
        
        if count == 0:
            return f"{header}No news articles found."
        
        article_texts = []
        for i, article in enumerate(articles):
            title = article["title"]
            source = article["source"]
            date_iso = article["published_date"]
            
            # Format the date in a readable way
            try:
                date_obj = datetime.fromisoformat(date_iso)
                # Today or yesterday?
                today = datetime.now().date()
                if date_obj.date() == today:
                    date_str = "Today, " + date_obj.strftime("%H:%M")
                elif date_obj.date() == today - timedelta(days=1):
                    date_str = "Yesterday, " + date_obj.strftime("%H:%M")
                else:
                    date_str = date_obj.strftime("%b %d, %Y")
            except:
                date_str = date_iso
            
            # Format the description
            desc = article.get("description", "")
            if len(desc) > 200:
                desc = desc[:197] + "..."
            
            article_text = f"{i+1}. {title}\n   Source: {source} | {date_str}\n"
            if desc:
                article_text += f"   {desc}\n"
            
            article_texts.append(article_text)
        
        # Join all article texts
        body = "\n".join(article_texts)
        
        return header + body

# Functions to expose to the LLM tool system
def search_news(query, max_results=5):
    """
    Search for news articles on a specific topic or keyword
    
    Args:
        query (str): The news topic or keyword to search for
        max_results (int, optional): Maximum number of results to return (default: 5)
        
    Returns:
        str: News search results in natural language
    """
    try:
        print(f"search_news function called with query: {query}, max_results: {max_results}")
        tool = NewsTool()
        news_data = tool.search_news(query, int(max_results))
        description = tool.get_news_description(news_data)
        print(f"News search completed with {len(news_data['articles'])} results")
        return description
    except Exception as e:
        error_msg = f"Error searching for news: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

def get_headlines(category="general", max_results=5):
    """
    Get the latest news headlines by category
    
    Args:
        category (str, optional): News category (default: "general")
        max_results (int, optional): Maximum number of results to return (default: 5)
        
    Returns:
        str: Latest headlines in natural language
    """
    try:
        print(f"get_headlines function called with category: {category}, max_results: {max_results}")
        tool = NewsTool()
        news_data = tool.get_headlines(category, int(max_results))
        description = tool.get_news_description(news_data)
        print(f"Headlines retrieved with {len(news_data['articles'])} results")
        return description
    except Exception as e:
        error_msg = f"Error getting headlines: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg