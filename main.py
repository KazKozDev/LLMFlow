import os
import re
import json
import requests
from typing import Dict, List, Any, Optional, Tuple, Union
import importlib.util
import inspect
from datetime import datetime

# Import tool modules from the tools directory
import sys
sys.path.append("./tools")  # Add tools directory to path if needed

# Attempt to import all tool modules
try:
    from currency_tool import convert_currency
    from geolocation_tool import get_location_info, calculate_distance, find_nearby_places
    from news_tool import search_news, get_headlines
    from stock_tool import get_stock_quote, get_company_info, get_historical_data, get_market_summary
    from time_tool import get_current_time, convert_time, get_time_difference, list_timezones
    from weather_tool import get_weather
    from wikipedia_tool import search_wikipedia, get_article_summary, get_article_content
    from web_parser_tool import parse_webpage, get_page_summary
    from search_tool import search_web
    from air_quality_tool import get_air_quality, get_air_quality_by_coordinates
    print("All tools imported successfully")
except ImportError as e:
    print(f"Error importing tools: {e}")
    # Continue without failing - we'll check for each tool's availability before using it

class Message:
    """Simple class to represent a message in the conversation."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, str]:
        """Convert message to dictionary format."""
        return {
            "role": self.role,
            "content": self.content
        }

class ConversationMemory:
    """Class to manage conversation history and context."""
    def __init__(self, max_messages: int = 10):
        """
        Initialize the conversation memory.
        
        Args:
            max_messages (int): Maximum number of messages to store
        """
        self.messages: List[Message] = []
        self.max_messages = max_messages
        self.user_info: Dict[str, Any] = {}
        self.recent_tools_used: List[Dict[str, Any]] = []
    
    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            role (str): The role of the sender (user/assistant)
            content (str): The message content
        """
        self.messages.append(Message(role, content))
        # Trim if exceeding max messages
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
    
    def add_tool_usage(self, tool: str, function: str, args: List[Any], result: str) -> None:
        """
        Record a tool usage in history.
        
        Args:
            tool (str): Tool name
            function (str): Function name
            args (List[Any]): Arguments used
            result (str): Result of the tool usage
        """
        tool_usage = {
            "tool": tool,
            "function": function,
            "args": args,
            "result": result,
            "timestamp": datetime.now()
        }
        self.recent_tools_used.append(tool_usage)
        # Keep only the last 5 tool usages
        if len(self.recent_tools_used) > 5:
            self.recent_tools_used.pop(0)
    
    def get_conversation_history(self, max_items: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Get the conversation history in a format suitable for the LLM.
        
        Args:
            max_items (Optional[int]): Maximum number of messages to return
            
        Returns:
            List[Dict[str, str]]: List of message dictionaries
        """
        if max_items is None:
            return [msg.to_dict() for msg in self.messages]
        else:
            return [msg.to_dict() for msg in self.messages[-max_items:]]
    
    def get_relevant_context(self) -> str:
        """
        Get a summary of relevant context about the conversation.
        
        Returns:
            str: Relevant context information
        """
        context = []
        
        # Add user information if available
        if self.user_info:
            user_info_str = "User information: " + ", ".join([f"{k}: {v}" for k, v in self.user_info.items()])
            context.append(user_info_str)
        
        # Add recent tool usage information
        if self.recent_tools_used:
            recent_tools = "\n".join([
                f"- Used {usage['tool']}.{usage['function']} with args: {', '.join(map(str, usage['args']))}"
                for usage in self.recent_tools_used[-3:]  # Just the last 3
            ])
            context.append(f"Recent tool usages:\n{recent_tools}")
        
        return "\n".join(context)
    
    def detect_language(self) -> Optional[str]:
        """
        Detect the language being used in the conversation.
        
        Returns:
            Optional[str]: Detected language code or None
        """
        if not self.messages:
            return None
        
        # Get the latest user message
        for msg in reversed(self.messages):
            if msg.role == "user":
                content = msg.content
                
                # Simple language detection based on character sets
                # Russian
                if re.search(r'[а-яА-Я]', content):
                    return "ru"
                
                # Chinese
                if re.search(r'[\u4e00-\u9fff]', content):
                    return "zh"
                
                # Japanese
                if re.search(r'[\u3040-\u30ff]', content):
                    return "ja"
                
                # Korean
                if re.search(r'[\uac00-\ud7a3]', content):
                    return "ko"
                
                # Arabic
                if re.search(r'[\u0600-\u06FF]', content):
                    return "ar"
                
                # Default to English
                return "en"
        
        return "en"  # Default to English

class LLMFlowAgent:
    """
    LLMFlowAgent uses an LLM to process queries, distinguishes between
    casual conversation and tool requests, and maintains conversation context.
    """
    
    def __init__(self, ollama_url="http://localhost:11434"):
        """
        Initialize the LLMFlowAgent.
        
        Args:
            ollama_url (str): URL for the LLM API
        """
        self.tools = self._discover_tools()
        self.ollama_url = ollama_url
        self.model = "gemma3:12b"
        self.memory = ConversationMemory()
        
        # Create tool descriptions for the LLM
        self.tool_descriptions = self._create_tool_descriptions()
        
    def _discover_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover available tools and their functions.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of tools and their functions
        """
        tools = {}
        
        # Define the tool modules and their main functions
        tool_modules = {
            "currency": {"module": "currency_tool", "functions": ["convert_currency"]},
            "geolocation": {"module": "geolocation_tool", "functions": ["get_location_info", "calculate_distance", "find_nearby_places"]},
            "news": {"module": "news_tool", "functions": ["search_news", "get_headlines"]},
            "stock": {"module": "stock_tool", "functions": ["get_stock_quote", "get_company_info", "get_historical_data", "get_market_summary"]},
            "time": {"module": "time_tool", "functions": ["get_current_time", "convert_time", "get_time_difference", "list_timezones"]},
            "weather": {"module": "weather_tool", "functions": ["get_weather"]},
            "wikipedia": {"module": "wikipedia_tool", "functions": ["search_wikipedia", "get_article_summary", "get_article_content"]},
            "web_parser": {"module": "web_parser_tool", "functions": ["parse_webpage", "get_page_summary"]},
            "search": {"module": "search_tool", "functions": ["search_web"]},
            "air_quality": {"module": "air_quality_tool", "functions": ["get_air_quality", "get_air_quality_by_coordinates"]},
        }
        
        # Check if each tool is available
        for tool_name, tool_info in tool_modules.items():
            module_name = tool_info["module"]
            try:
                # Try to import the module
                module = importlib.import_module(module_name)
                
                # Get the functions from the module
                tool_functions = {}
                for func_name in tool_info["functions"]:
                    if hasattr(module, func_name):
                        tool_functions[func_name] = getattr(module, func_name)
                
                # Add the tool to the available tools
                if tool_functions:
                    tools[tool_name] = {
                        "module": module,
                        "functions": tool_functions
                    }
                    print(f"Loaded tool: {tool_name} with {len(tool_functions)} functions")
            except (ImportError, AttributeError) as e:
                print(f"Could not load tool {tool_name}: {e}")
        
        return tools
    
    def _create_tool_descriptions(self) -> Dict[str, Dict[str, Any]]:
        """
        Create descriptions of tools and their functions for the LLM.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary of tool descriptions
        """
        # Tool descriptions and their function signatures
        tool_descriptions = {
            "currency": {
                "description": "Convert amounts between different currencies using real-time exchange rates",
                "functions": {
                    "convert_currency": {
                        "description": "Convert an amount from one currency to another",
                        "arguments": ["amount", "from_currency", "to_currency"],
                        "example": "convert_currency(100, 'USD', 'EUR')"
                    }
                }
            },
            "geolocation": {
                "description": "Provides geographic information about locations, distances, and points of interest",
                "functions": {
                    "get_location_info": {
                        "description": "Get detailed information about a location",
                        "arguments": ["location"],
                        "example": "get_location_info('Paris, France')"
                    },
                    "calculate_distance": {
                        "description": "Calculate the distance between two locations",
                        "arguments": ["location1", "location2"],
                        "example": "calculate_distance('New York', 'Los Angeles')"
                    },
                    "find_nearby_places": {
                        "description": "Find nearby places of a particular category",
                        "arguments": ["location", "category", "radius_km(optional)"],
                        "example": "find_nearby_places('Tokyo', 'restaurants', 2)"
                    }
                }
            },
            "news": {
                "description": "Retrieves the latest news from multiple sources using RSS feeds",
                "functions": {
                    "search_news": {
                        "description": "Search for news articles on a specific topic",
                        "arguments": ["query", "max_results(optional)"],
                        "example": "search_news('climate change', 5)"
                    },
                    "get_headlines": {
                        "description": "Get the latest headlines by category",
                        "arguments": ["category", "max_results(optional)"],
                        "example": "get_headlines('technology', 5)"
                    }
                }
            },
            "stock": {
                "description": "Retrieves financial market data about stocks, indices, and companies",
                "functions": {
                    "get_stock_quote": {
                        "description": "Get current stock quote for a symbol",
                        "arguments": ["symbol"],
                        "example": "get_stock_quote('AAPL')"
                    },
                    "get_company_info": {
                        "description": "Get detailed information about a company",
                        "arguments": ["symbol"],
                        "example": "get_company_info('MSFT')"
                    },
                    "get_historical_data": {
                        "description": "Get historical stock data",
                        "arguments": ["symbol", "period"],
                        "example": "get_historical_data('GOOGL', '1month')"
                    },
                    "get_market_summary": {
                        "description": "Get a summary of current market conditions",
                        "arguments": [],
                        "example": "get_market_summary()"
                    }
                }
            },
            "time": {
                "description": "Provides time-related information for different timezones",
                "functions": {
                    "get_current_time": {
                        "description": "Get current time for a location",
                        "arguments": ["location"],
                        "example": "get_current_time('Tokyo')"
                    },
                    "convert_time": {
                        "description": "Convert time between locations",
                        "arguments": ["time_string", "source_location", "target_location"],
                        "example": "convert_time('3pm', 'New York', 'London')"
                    },
                    "get_time_difference": {
                        "description": "Get time difference between locations",
                        "arguments": ["location1", "location2"],
                        "example": "get_time_difference('Paris', 'Los Angeles')"
                    },
                    "list_timezones": {
                        "description": "List available timezones for a region",
                        "arguments": ["region(optional)"],
                        "example": "list_timezones('Europe')"
                    }
                }
            },
            "weather": {
                "description": "Retrieves current weather data for any location",
                "functions": {
                    "get_weather": {
                        "description": "Get current weather for a location",
                        "arguments": ["location"],
                        "example": "get_weather('London')"
                    }
                }
            },
            "wikipedia": {
                "description": "Retrieves information from Wikipedia articles in multiple languages",
                "functions": {
                    "search_wikipedia": {
                        "description": "Search Wikipedia for articles",
                        "arguments": ["query", "language(optional)", "limit(optional)"],
                        "example": "search_wikipedia('quantum physics', 'en', 5)"
                    },
                    "get_article_summary": {
                        "description": "Get a summary of a Wikipedia article",
                        "arguments": ["title", "language(optional)"],
                        "example": "get_article_summary('Albert Einstein')"
                    },
                    "get_article_content": {
                        "description": "Get content from a Wikipedia article",
                        "arguments": ["title", "language(optional)", "sections(optional)"],
                        "example": "get_article_content('Machine Learning', 'en', 'History,Applications')"
                    }
                }
            },
            "web_parser": {
                "description": "Extracts and cleans the main content from web pages",
                "functions": {
                    "parse_webpage": {
                        "description": "Parse a webpage and extract its main content",
                        "arguments": ["url"],
                        "example": "parse_webpage('https://example.com/article')"
                    },
                    "get_page_summary": {
                        "description": "Get a summary of a webpage's content",
                        "arguments": ["url"],
                        "example": "get_page_summary('https://example.com/news')"
                    }
                }
            },
            "search": {
                "description": "Search the web for information on any topic using DuckDuckGo",
                "functions": {
                    "search_web": {
                        "description": "Search the web for information on a topic",
                        "arguments": ["query", "num_results(optional)"],
                        "example": "search_web('latest developments in artificial intelligence', 5)"
                    }
                }
            },
            "air_quality": {
                "description": "Retrieves current air quality data for locations worldwide",
                "functions": {
                    "get_air_quality": {
                        "description": "Get air quality information for a specified location",
                        "arguments": ["location"],
                        "example": "get_air_quality('Beijing')"
                    },
                    "get_air_quality_by_coordinates": {
                        "description": "Get air quality information for specified coordinates",
                        "arguments": ["latitude", "longitude"],
                        "example": "get_air_quality_by_coordinates(40.7128, -74.0060)"
                    }
                }
            }
        }
        
        # Filter to only include available tools
        descriptions = {}
        for tool_name, tool_desc in tool_descriptions.items():
            if tool_name in self.tools:
                descriptions[tool_name] = tool_desc
        
        return descriptions
    
    def query_llm(self, prompt: str) -> str:
        """
        Query the LLM with a given prompt.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: The LLM's response
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            print(f"Error querying LLM: {str(e)}")
            return f"Error: Could not query the LLM - {str(e)}"
    
    def determine_query_type(self, query: str) -> Dict[str, Any]:
        """
        Use the LLM to determine if the user's query is a tool request or casual conversation.
        
        Args:
            query (str): The user's query
            
        Returns:
            Dict[str, Any]: Query classification info
        """
        # Get conversation history for context
        conversation_history = self.memory.get_conversation_history(max_items=5)
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in conversation_history
        ])
        
        # Detect the language
        language = self.memory.detect_language() or "en"
        
        # Create the prompt
        prompt = f"""You are an assistant that can handle casual conversations and also use tools to provide information.

First, determine if the user's query requires using a tool or if it's just a casual conversation.

Available tool categories:
- Currency conversion
- Geolocation and places
- News retrieval
- Stock market information
- Time and timezone data
- Weather information
- Wikipedia knowledge
- Web page parsing
- Web search
- Air quality information

Detected language: {language}

Recent conversation:
{conversation_text}

User query: "{query}"

Respond with a JSON object containing the following fields:
- "query_type": Either "tool_request" or "casual_conversation"
- "explanation": Brief explanation for the classification
- "language": The detected language of the query
- "translation": If the query is not in English, provide an English translation

Format:
{{
  "query_type": "tool_request" or "casual_conversation",
  "explanation": "Explanation for the classification",
  "language": "language_code",
  "translation": "English translation if needed, otherwise null"
}}

DO NOT include any other text in your response, ONLY the JSON object.
"""

        # Get the LLM's response
        llm_response = self.query_llm(prompt)
        
        try:
            # Extract the JSON part of the response
            json_match = re.search(r'(\{.*\})', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                
                print(f"Query classification: {result.get('query_type')}")
                print(f"Explanation: {result.get('explanation')}")
                
                return result
            else:
                print("Could not extract JSON from LLM response")
                print(f"Raw response: {llm_response}")
                return {
                    "query_type": "casual_conversation",  # Default to casual if JSON parsing fails
                    "explanation": "Failed to parse LLM response",
                    "language": language,
                    "translation": None
                }
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            print(f"Raw response: {llm_response}")
            return {
                "query_type": "casual_conversation",  # Default to casual if JSON parsing fails
                "explanation": f"Error: {str(e)}",
                "language": language,
                "translation": None
            }
    
    def analyze_tool_query(self, query: str, translation: Optional[str] = None) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Analyze a tool request query to determine which tool, function, and arguments to use.
        
        Args:
            query (str): The user's query
            translation (Optional[str]): English translation of the query, if applicable
            
        Returns:
            Tuple[Optional[str], Optional[str], List[str]]: 
                (tool_name, function_name, arguments) or (None, None, []) if no match
        """
        # Use the translation if available
        effective_query = translation if translation else query
        
        # Create a prompt for the LLM
        tools_json = json.dumps(self.tool_descriptions, indent=2)
        
        prompt = f"""You are a tool-use assistant. Analyze the user query and determine which tool and function to use.

Available tools:
{tools_json}

Original user query: "{query}"
Translated query (if applicable): "{effective_query}"

Respond ONLY with a JSON object containing the following fields:
- "tool": The name of the tool to use
- "function": The function name to call
- "arguments": An array of argument values in the correct order for the function
- "reasoning": A brief explanation of your selection

Format:
{{
  "tool": "tool_name",
  "function": "function_name",
  "arguments": ["arg1", "arg2", ...],
  "reasoning": "Explanation for why this tool and function were selected"
}}

DO NOT include any other text in your response, ONLY the JSON object.
"""

        # Get the LLM's response
        llm_response = self.query_llm(prompt)
        
        try:
            # Extract the JSON part of the response
            json_match = re.search(r'(\{.*\})', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result = json.loads(json_str)
                
                tool_name = result.get("tool")
                function_name = result.get("function")
                arguments = result.get("arguments", [])
                reasoning = result.get("reasoning", "No reasoning provided")
                
                print(f"LLM reasoning: {reasoning}")
                
                return tool_name, function_name, arguments
            else:
                print("Could not extract JSON from LLM response")
                print(f"Raw response: {llm_response}")
                return None, None, []
        except Exception as e:
            print(f"Error parsing LLM response: {str(e)}")
            print(f"Raw response: {llm_response}")
            return None, None, []
    
    def execute_tool(self, tool_name: str, function_name: str, args: List[Any]) -> str:
        """
        Execute a tool function with the provided arguments.
        
        Args:
            tool_name (str): Name of the tool
            function_name (str): Name of the function to call
            args (List[Any]): Arguments to pass to the function
            
        Returns:
            str: Result from the tool
        """
        if tool_name not in self.tools or function_name not in self.tools[tool_name]["functions"]:
            return f"Error: Tool '{tool_name}' or function '{function_name}' not available"
        
        # Get the function to call
        func = self.tools[tool_name]["functions"][function_name]
        
        try:
            # Get the function's signature to determine how many arguments it expects
            sig = inspect.signature(func)
            params = list(sig.parameters.values())
            min_args = sum(1 for param in params if param.default == param.empty and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD))
            
            # Check if we have enough arguments
            if len(args) < min_args:
                return f"Error: Not enough arguments for {function_name}, need at least {min_args}, got {len(args)}"
            
            # Call the function with the provided arguments
            result = func(*args[:len(params)])
            
            # Add to memory
            self.memory.add_tool_usage(tool_name, function_name, args, result)
            
            return result
        except Exception as e:
            return f"Error executing {function_name}: {str(e)}"
    
    def handle_casual_conversation(self, query: str, query_info: Dict[str, Any]) -> str:
        """
        Use the LLM to respond to casual conversation.
        
        Args:
            query (str): The user's query
            query_info (Dict[str, Any]): Information about the query
            
        Returns:
            str: Response to the casual conversation
        """
        # Get conversation history for context
        conversation_history = self.memory.get_conversation_history(max_items=5)
        conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        
        # Get any relevant context
        relevant_context = self.memory.get_relevant_context()
        
        # Detect the language to respond in
        language = query_info.get("language", "en")
        
        prompt = f"""You are a helpful and friendly conversational assistant. Respond to the user's message naturally and engagingly.

Recent conversation:
{conversation_text}

{relevant_context if relevant_context else ""}

User's message: "{query}"

Guidelines:
- Be natural, friendly, and conversational
- If the user is greeting you, greet them back
- If the user is speaking in a language other than English, respond in the same language
- Keep your response concise, not more than 2-3 paragraphs
- Don't offer to use tools unless the user specifically asks about your capabilities

Detected language: {language}
Respond directly to the user in their language.
"""

        # Get the LLM's response
        response = self.query_llm(prompt)
        
        return response
    
    def process_query(self, query: str) -> str:
        """
        Process a user query and return the result.
        
        Args:
            query (str): The user's query
            
        Returns:
            str: Response to the query
        """
        # Add the query to memory
        self.memory.add_message("user", query)
        
        # First, determine if this is a tool request or casual conversation
        query_info = self.determine_query_type(query)
        query_type = query_info.get("query_type", "casual_conversation")
        translation = query_info.get("translation")
        
        # Handle based on query type
        if query_type == "tool_request":
            # Analyze the query to determine tool and function
            tool_name, function_name, args = self.analyze_tool_query(query, translation)
            
            if not tool_name or not function_name:
                response = "I understand you're asking me to use a tool, but I'm not sure which one would help. Could you please be more specific about what information you're looking for?"
            else:
                # Execute the tool
                print(f"Using tool: {tool_name}, function: {function_name}, args: {args}")
                response = self.execute_tool(tool_name, function_name, args)
        else:
            # Handle casual conversation
            response = self.handle_casual_conversation(query, query_info)
        
        # Add response to memory
        self.memory.add_message("assistant", response)
        
        return response

# Interactive CLI for testing the agent
def main():
    print("Starting the LLMFlowAgent...")
    agent = LLMFlowAgent()
    print(f"Agent started with {len(agent.tools)} available tools")
    
    print("\nYou can make queries such as:")
    print("- 'What's the weather in Madrid?'")
    print("- 'Convert 100 USD to EUR'")
    print("- 'What are the latest technology news?'")
    print("- 'What time is it in Tokyo?'")
    print("- 'Tell me about quantum computing'")
    print("- 'Parse this webpage: https://example.com/article'")
    print("- 'Search the web for latest AI developments'")
    print("- 'How's the air quality in Beijing?'")
    print("- Or simply chat with me like 'Hello, how are you?'")
    print("\nType 'exit' or 'quit' to end.")
    
    while True:
        try:
            query = input("\nQuery: ")
            if query.lower() in ["exit", "quit", "q"]:
                break
                
            response = agent.process_query(query)
            print("\nResponse:")
            print(response)
        except UnicodeDecodeError:
            print("\nError: Unable to decode input. Please check your terminal encoding settings.")
            continue
        except Exception as e:
            print(f"\nError occurred: {str(e)}")
            continue
    
    print("Thank you for using the LLMFlowAgent!")

if __name__ == "__main__":
    main()
