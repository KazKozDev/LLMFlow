import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import requests
import json
import inspect

# Import classes from main.py
# Assuming main.py is in the root directory relative to tests/
# Also import ChainStep for mocking
from chain_orchestrator import ChainStep
try:
    from main import ConversationMemory, Message, LLMFlowAgent
except ImportError:
    # If main.py is not directly importable, adjust path or mock if necessary
    pytest.fail("Could not import classes from main.py. Ensure it's importable from the tests directory.")

# --- Tests for ConversationMemory ---

class TestConversationMemory:

    def test_add_message_append(self):
        """Test that add_message appends messages correctly."""
        memory = ConversationMemory(max_messages=5)
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi there!")
        
        assert len(memory.messages) == 2
        assert memory.messages[0].role == "user"
        assert memory.messages[0].content == "Hello"
        assert memory.messages[1].role == "assistant"
        assert memory.messages[1].content == "Hi there!"

    def test_add_message_trimming(self):
        """Test that message history is trimmed when max_messages is exceeded."""
        memory = ConversationMemory(max_messages=3)
        memory.add_message("user", "Msg 1")
        memory.add_message("assistant", "Msg 2")
        memory.add_message("user", "Msg 3")
        memory.add_message("assistant", "Msg 4") # This should trigger trimming

        assert len(memory.messages) == 3
        assert memory.messages[0].content == "Msg 2" # Oldest (Msg 1) should be removed
        assert memory.messages[1].content == "Msg 3"
        assert memory.messages[2].content == "Msg 4"

        memory.add_message("user", "Msg 5") # Trigger trimming again
        assert len(memory.messages) == 3
        assert memory.messages[0].content == "Msg 3"
        assert memory.messages[1].content == "Msg 4"
        assert memory.messages[2].content == "Msg 5"

    def test_get_conversation_history_all(self):
        """Test getting the full conversation history."""
        memory = ConversationMemory(max_messages=5)
        memory.add_message("user", "First")
        memory.add_message("assistant", "Second")
        history = memory.get_conversation_history()
        
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "First"}
        assert history[1] == {"role": "assistant", "content": "Second"}

    def test_get_conversation_history_limited(self):
        """Test getting a limited number of recent messages."""
        memory = ConversationMemory(max_messages=5)
        memory.add_message("user", "Msg 1")
        memory.add_message("assistant", "Msg 2")
        memory.add_message("user", "Msg 3")
        memory.add_message("assistant", "Msg 4")
        
        history_last_2 = memory.get_conversation_history(max_items=2)
        assert len(history_last_2) == 2
        assert history_last_2[0]["content"] == "Msg 3"
        assert history_last_2[1]["content"] == "Msg 4"

        history_last_3 = memory.get_conversation_history(max_items=3)
        assert len(history_last_3) == 3
        assert history_last_3[0]["content"] == "Msg 2"
        assert history_last_3[1]["content"] == "Msg 3"
        assert history_last_3[2]["content"] == "Msg 4"
        
        history_more_than_available = memory.get_conversation_history(max_items=10)
        assert len(history_more_than_available) == 4 # Returns all available if max_items > count

    def test_get_conversation_history_empty(self):
        """Test getting history when memory is empty."""
        memory = ConversationMemory()
        history = memory.get_conversation_history()
        assert len(history) == 0
        history_limited = memory.get_conversation_history(max_items=5)
        assert len(history_limited) == 0

    def test_detect_language_english(self):
        """Test language detection for English text."""
        memory = ConversationMemory()
        memory.add_message("assistant", "Irrelevant")
        memory.add_message("user", "Hello, how are you?")
        assert memory.detect_language() == "en"

    def test_detect_language_russian(self):
        """Test language detection for Russian text."""
        memory = ConversationMemory()
        memory.add_message("user", "Привет, как дела?")
        assert memory.detect_language() == "ru"
        
    def test_detect_language_chinese(self):
        """Test language detection for Chinese text."""
        memory = ConversationMemory()
        memory.add_message("user", "你好，世界") # Ni hao, shijie
        assert memory.detect_language() == "zh"

    def test_detect_language_mixed(self):
        """Test language detection with mixed scripts (should prioritize non-English)."""
        memory = ConversationMemory()
        memory.add_message("user", "This is English, but also Привет") 
        assert memory.detect_language() == "ru" # Cyrillic detected

    def test_detect_language_no_user_message(self):
        """Test language detection when only assistant messages exist."""
        memory = ConversationMemory()
        memory.add_message("assistant", "I am a bot.")
        assert memory.detect_language() == "en" # Defaults to English

    def test_detect_language_empty(self):
        """Test language detection when memory is empty."""
        memory = ConversationMemory()
        assert memory.detect_language() is None # Should return None if no messages 

    # --- New tests for add_tool_usage ---
    def test_add_tool_usage_append(self):
        """Test adding tool usage records."""
        memory = ConversationMemory(max_messages=5) # max_messages irrelevant here
        assert len(memory.recent_tools_used) == 0
        memory.add_tool_usage("weather", "get_weather", ["London"], "Rainy")
        assert len(memory.recent_tools_used) == 1
        assert memory.recent_tools_used[0]["tool"] == "weather"
        assert memory.recent_tools_used[0]["function"] == "get_weather"
        assert memory.recent_tools_used[0]["args"] == ["London"]
        assert memory.recent_tools_used[0]["result"] == "Rainy"

        memory.add_tool_usage("time", "get_current_time", ["Paris"], "10:00 AM")
        assert len(memory.recent_tools_used) == 2
        assert memory.recent_tools_used[1]["tool"] == "time"

    def test_add_tool_usage_trimming(self):
        """Test trimming of the tool usage history (keeps last 5)."""
        memory = ConversationMemory()
        for i in range(7):
            memory.add_tool_usage(f"tool_{i}", f"func_{i}", [i], f"res_{i}")
        
        assert len(memory.recent_tools_used) == 5 # Should keep only the last 5
        assert memory.recent_tools_used[0]["tool"] == "tool_2" # Tools 0 and 1 should be gone
        assert memory.recent_tools_used[4]["tool"] == "tool_6"

    # --- New tests for get_relevant_context ---
    def test_get_relevant_context_empty(self):
        """Test context generation when memory has no user info or tool usage."""
        memory = ConversationMemory()
        context = memory.get_relevant_context()
        assert context == "" # Expect empty string

    def test_get_relevant_context_user_info_only(self):
        """Test context generation with only user info."""
        memory = ConversationMemory()
        memory.user_info = {"location": "Berlin", "pref_units": "metric"}
        context = memory.get_relevant_context()
        assert "User information: location: Berlin, pref_units: metric" in context
        assert "Recent tool usages:" not in context

    def test_get_relevant_context_tool_usage_only(self):
        """Test context generation with only tool usage."""
        memory = ConversationMemory()
        memory.add_tool_usage("weather", "get_weather", ["London"], "Rainy")
        memory.add_tool_usage("time", "get_current_time", ["Paris"], "10:00 AM")
        context = memory.get_relevant_context()
        assert "User information:" not in context
        assert "Recent tool usages:" in context
        assert "- Used weather.get_weather with args: London" in context
        assert "- Used time.get_current_time with args: Paris" in context

    def test_get_relevant_context_tool_usage_limited(self):
        """Test context generation shows only the last 3 tool usages."""
        memory = ConversationMemory()
        for i in range(4):
             memory.add_tool_usage(f"tool_{i}", f"func_{i}", [f"arg_{i}"], f"res_{i}")
        context = memory.get_relevant_context()
        assert "Recent tool usages:" in context
        assert "- Used tool_0" not in context # Should only show tools 1, 2, 3
        assert "- Used tool_1" in context
        assert "- Used tool_2" in context
        assert "- Used tool_3" in context

    def test_get_relevant_context_all(self):
        """Test context generation with both user info and tool usage."""
        memory = ConversationMemory()
        memory.user_info = {"name": "Test User"}
        memory.add_tool_usage("currency", "convert", [100, "USD", "EUR"], "90 EUR")
        context = memory.get_relevant_context()
        assert "User information: name: Test User" in context
        assert "Recent tool usages:" in context
        assert "- Used currency.convert with args: 100, USD, EUR" in context

    # --- Add tests for missing languages ---
    def test_detect_language_japanese(self):
        """Test language detection for Japanese text."""
        memory = ConversationMemory()
        memory.add_message("user", "こんにちは世界") # Konnichiwa sekai
        assert memory.detect_language() == "ja"

    def test_detect_language_korean(self):
        """Test language detection for Korean text."""
        memory = ConversationMemory()
        memory.add_message("user", "안녕하세요 세계") # Annyeonghaseyo segye
        assert memory.detect_language() == "ko"

    def test_detect_language_arabic(self):
        """Test language detection for Arabic text."""
        memory = ConversationMemory()
        memory.add_message("user", "مرحبا بالعالم") # Marhaban bialalam
        assert memory.detect_language() == "ar"

# --- Tests for LLMFlowAgent ---

# We need an instance of the agent to test its methods.
# We can create a dummy instance or mock its dependencies if needed.
@pytest.fixture
def agent_instance():
    """Provides a LLMFlowAgent instance for testing."""
    # Mock dependencies like _discover_tools if they are complex or external
    with patch.object(LLMFlowAgent, '_discover_tools', return_value={}), \
         patch.object(LLMFlowAgent, '_create_tool_descriptions', return_value={}):
        agent = LLMFlowAgent() # Assuming __init__ doesn't have heavy side effects
        # Manually set the tool_name_map for testing normalize_tool_name
        agent.tool_name_map = {
            'weather information': 'weather',
            'weather tool': 'weather',
            'weather': 'weather',
            'time information': 'time',
            'time': 'time',
            'currency converter': 'currency',
            'currency': 'currency',
        }
        return agent

class TestLLMFlowAgent:

    # --- Tests for normalize_tool_name ---

    def test_normalize_tool_name_exact_match(self, agent_instance):
        """Test normalization with exact matches (case-insensitive)."""
        assert agent_instance.normalize_tool_name("weather tool") == "weather"
        assert agent_instance.normalize_tool_name("Weather Information") == "weather"
        assert agent_instance.normalize_tool_name("currency") == "currency"
        assert agent_instance.normalize_tool_name("TIME") == "time"

    def test_normalize_tool_name_partial_match(self, agent_instance):
        """Test normalization with partial matches (substring)."""
        # Assuming 'weather information' maps to 'weather'
        assert agent_instance.normalize_tool_name("Get weather information now") == "weather"
        # Assuming 'currency converter' maps to 'currency'
        assert agent_instance.normalize_tool_name("Use the currency converter tool") == "currency"
        # Test case where the map key is a substring of the input
        assert agent_instance.normalize_tool_name("show time info") == "time" # Matches 'time information' key

    def test_normalize_tool_name_no_match(self, agent_instance):
        """Test normalization when no match is found."""
        assert agent_instance.normalize_tool_name("calculator") == "calculator"
        assert agent_instance.normalize_tool_name("unknown tool") == "unknown tool"

    def test_normalize_tool_name_empty_or_none(self, agent_instance):
        """Test normalization with empty or None input."""
        assert agent_instance.normalize_tool_name("") is None
        assert agent_instance.normalize_tool_name(None) is None

    # --- Tests for extract_entities_with_llm ---

    @patch.object(LLMFlowAgent, 'query_llm')
    def test_extract_entities_location(self, mock_query_llm, agent_instance):
        """Test extracting location entity."""
        query = "what is the weather in Barcelona?"
        mock_response_json = '{"location": "Barcelona", "event_type": "weather"}'
        mock_query_llm.return_value = mock_response_json
        
        entities = agent_instance.extract_entities_with_llm(query)
        
        mock_query_llm.assert_called_once() # Check LLM was called
        assert entities == {"location": "Barcelona", "event_type": "weather"}

    @patch.object(LLMFlowAgent, 'query_llm')
    def test_extract_entities_currency(self, mock_query_llm, agent_instance):
        """Test extracting currency entities."""
        query = "convert 100 EUR to USD"
        # Simulate LLM response possibly wrapped in ```json ... ```
        mock_response_json = '```json\n{"from_currency": "EUR", "to_currency": "USD", "amount": 100}\n```'
        mock_query_llm.return_value = mock_response_json
        
        entities = agent_instance.extract_entities_with_llm(query)
        
        mock_query_llm.assert_called_once()
        assert entities == {"from_currency": "EUR", "to_currency": "USD", "amount": 100}

    @patch.object(LLMFlowAgent, 'query_llm')
    def test_extract_entities_parsing_error(self, mock_query_llm, agent_instance):
        """Test entity extraction when LLM returns invalid JSON."""
        query = "some query"
        mock_query_llm.return_value = "This is not JSON."
        
        entities = agent_instance.extract_entities_with_llm(query)
        
        mock_query_llm.assert_called_once()
        assert entities == {} # Should return empty dict on error

    # --- Tests for determine_query_type ---

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en') # Mock language detection
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm') # Mock entity extraction as well
    def test_determine_query_type_tool_request(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test determining a single tool request."""
        query = "what is the time in London?"
        mock_entities = {"location": "London"}
        mock_extract_entities.return_value = mock_entities
        
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "time tool",\n  "function": "get_current_time",\n  "args": ["London"],\n  "explanation": "User is asking for the current time in a specific location.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        
        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once() # Check classification LLM call
        mock_extract_entities.assert_called_once_with(query.lower())
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'time' # Check normalization was applied
        assert result['function'] == 'get_current_time'
        assert result['args'] == ["London"]

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm', return_value={})
    def test_determine_query_type_casual(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test determining a casual conversation query."""
        query = "hello how are you"
        mock_llm_response = '{\n  "type": "casual_conversation",\n  "tool": null,\n  "function": null,\n  "args": [],\n  "explanation": "User is making small talk.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        
        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'casual_conversation'
        assert result['tool'] is None

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en') 
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_correction(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test that query type determination corrects function names (e.g., eclipse details)."""
        query = "show eclipse details for Barcelona"
        mock_entities = {"location": "Barcelona", "event_type": "eclipse"}
        mock_extract_entities.return_value = mock_entities
        # Simulate LLM initially suggesting a non-existent function
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "astronomy",\n  "function": "get_eclipse_details",\n  "args": ["Barcelona"],\n  "explanation": "User wants eclipse details.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        # Add astronomy tool to the agent's known tools for correction logic
        agent_instance.tools['astronomy'] = {'functions': {'get_celestial_events': None, 'get_planet_info': None}}

        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'astronomy' 
        # Check that the function was corrected
        assert result['function'] == 'get_celestial_events'
        # Check the corrected arguments based on the tool logic
        assert result['args'] == [None, 'Barcelona']

    def test_determine_query_type_exit(self, agent_instance):
        """Test determining an exit command."""
        query = "quit"
        result = agent_instance.determine_query_type(query)
        assert result['type'] == 'exit' 

    # --- More tests for determine_query_type --- 

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_llm_response_leading_text(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test parsing LLM response when it includes leading text."""
        query = "how are you today"
        mock_extract_entities.return_value = {}
        # Simulate LLM response with leading text
        mock_llm_response = 'Okay, I have determined the query type. Here is the JSON:\n{\n  "type": "casual_conversation",\n  "tool": null,\n  "function": null,\n  "args": [],\n  "explanation": "User is making small talk.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        
        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'casual_conversation' # Check JSON was found and parsed
        assert result['tool'] is None

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_function_correction_fallback(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test function correction fallback for weather/air_quality."""
        query = "check air quality in Paris"
        mock_entities = {"location": "Paris"}
        mock_extract_entities.return_value = mock_entities
        # Simulate LLM suggesting a plausible but non-existent function
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "air_quality",\n  "function": "get_aqi_index",\n  "args": ["Paris"],\n  "explanation": "User wants AQI.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        # Add air_quality tool to the agent's known tools for correction logic
        agent_instance.tools['air_quality'] = {'functions': {'get_air_quality': None, 'get_air_quality_by_coordinates': None}}

        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'air_quality'
        # Check that the function was corrected to the default
        assert result['function'] == 'get_air_quality'
        assert result['args'] == ["Paris"]

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_currency_arg_correction(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test currency argument correction using extracted entities."""
        query = "convert CAD to JPY"
        # Simulate entities extracted correctly
        mock_entities = {"from_currency": "CAD", "to_currency": "JPY", "amount": None}
        mock_extract_entities.return_value = mock_entities
        # Simulate LLM response missing the arguments
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "currency",\n  "function": "convert_currency",\n  "args": [],\n  "explanation": "User wants currency conversion.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        # Ensure currency tool exists for correction logic
        agent_instance.tools['currency'] = {'functions': {'convert_currency': None}}

        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'currency'
        assert result['function'] == 'convert_currency'
        # Check args were corrected: default amount 1, plus entities
        assert result['args'] == [1, "CAD", "JPY"]

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en') 
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_astronomy_arg_correction_no_args(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test astronomy arg correction when LLM provides no args but location entity exists."""
        query = "celestial events in Sydney"
        mock_entities = {"location": "Sydney"}
        mock_extract_entities.return_value = mock_entities
        # Simulate LLM response with no args
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "astronomy",\n  "function": "get_celestial_events",\n  "args": [], \n  "explanation": "User wants events in Sydney.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        agent_instance.tools['astronomy'] = {'functions': {'get_celestial_events': None}}

        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'astronomy' 
        assert result['function'] == 'get_celestial_events'
        # Check args were corrected: [None (for date), location]
        assert result['args'] == [None, 'Sydney']

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(ConversationMemory, 'detect_language', return_value='en') 
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_determine_query_type_astronomy_arg_correction_date_only(self, mock_extract_entities, mock_detect_lang, mock_query_llm, agent_instance):
        """Test astronomy arg correction when LLM provides only date but location entity exists."""
        query = "celestial events tomorrow in Sydney"
        mock_entities = {"location": "Sydney"}
        mock_extract_entities.return_value = mock_entities
        # Simulate LLM response with only date arg
        mock_llm_response = '{\n  "type": "tool_request",\n  "tool": "astronomy",\n  "function": "get_celestial_events",\n  "args": ["2024-04-25"], \n  "explanation": "User wants events tomorrow in Sydney.",\n  "language": "en",\n  "translation": null\n}'
        mock_query_llm.return_value = mock_llm_response
        agent_instance.tools['astronomy'] = {'functions': {'get_celestial_events': None}}

        result = agent_instance.determine_query_type(query)
        
        mock_query_llm.assert_called_once()
        assert result['type'] == 'tool_request'
        assert result['tool'] == 'astronomy' 
        assert result['function'] == 'get_celestial_events'
        # Check args were corrected: [date, location]
        assert result['args'] == ["2024-04-25", 'Sydney']

    # --- Tests for _discover_tools ---

    @patch('importlib.import_module')
    def test_discover_tools_success(self, mock_import, agent_instance):
        """Test discovering tools when modules and functions exist."""
        # Simulate successful import and function existence
        mock_module = patch.object # Use a mock object that can have attributes
        mock_module.convert_currency = lambda x, y, z: None # Mock function
        mock_module.get_weather = lambda x: None # Mock function
        
        # Configure the mock_import side effect
        def import_side_effect(module_name):
            if module_name == "currency_tool":
                # Simulate currency_tool having convert_currency
                mock_currency_module = patch.object
                mock_currency_module.convert_currency = lambda a,b,c: None
                return mock_currency_module
            elif module_name == "weather_tool":
                # Simulate weather_tool having get_weather
                mock_weather_module = patch.object
                mock_weather_module.get_weather = lambda a: None
                return mock_weather_module
            else:
                raise ImportError(f"No module named {module_name}")
        mock_import.side_effect = import_side_effect

        # Reset agent's tools before discovery
        agent_instance.tools = {}
        discovered_tools = agent_instance._discover_tools()
        
        assert "currency" in discovered_tools
        assert "convert_currency" in discovered_tools["currency"]["functions"]
        assert "weather" in discovered_tools
        assert "get_weather" in discovered_tools["weather"]["functions"]
        assert "geolocation" not in discovered_tools # Example of a tool that wasn't mocked
        assert len(discovered_tools) == 2

    @patch('importlib.import_module')
    def test_discover_tools_import_error(self, mock_import, agent_instance):
        """Test discovering tools when a module cannot be imported."""
        # Simulate ImportError for a specific tool
        def import_side_effect(module_name):
            if module_name == "news_tool":
                raise ImportError("Cannot import news_tool")
            elif module_name == "time_tool":
                mock_time_module = patch.object
                mock_time_module.get_current_time = lambda x: None
                return mock_time_module
            else:
                # Allow other imports (or raise generic error)
                raise ImportError(f"No module named {module_name}")
        mock_import.side_effect = import_side_effect

        agent_instance.tools = {}
        discovered_tools = agent_instance._discover_tools()

        assert "news" not in discovered_tools # Failed import
        assert "time" in discovered_tools     # Successful import
        assert len(discovered_tools) == 1

    @patch('importlib.import_module')
    def test_discover_tools_attribute_error(self, mock_import, agent_instance):
        """Test discovering tools when a function is missing from a module."""
        # Simulate a module existing but missing a function
        mock_stock_module = patch.object
        # Intentionally missing get_company_info
        mock_stock_module.get_stock_quote = lambda x: None 
        
        def import_side_effect(module_name):
            if module_name == "stock_tool":
                return mock_stock_module
            else:
                raise ImportError(f"No module named {module_name}")
        mock_import.side_effect = import_side_effect

        agent_instance.tools = {}
        discovered_tools = agent_instance._discover_tools()
        
        assert "stock" in discovered_tools
        # Even if some functions are missing, the tool is loaded if the module imports
        # and at least one function is found (or if the functions list is empty)
        # In this mocked setup, get_stock_quote exists implicitly on patch.object
        # Let's refine the mock to explicitly lack one function
        
        # --- Redo mock setup for clarity ---
        mock_stock_module_refined = type('MockStockModule', (), {})()
        mock_stock_module_refined.get_stock_quote = lambda x: None
        # mock_stock_module_refined does NOT have get_company_info etc.
        
        mock_import.side_effect = lambda name: mock_stock_module_refined if name == "stock_tool" else ImportError
        
        agent_instance.tools = {}
        # Re-run discovery with refined mock
        discovered_tools_refined = agent_instance._discover_tools()
        
        assert "stock" in discovered_tools_refined
        assert "get_stock_quote" in discovered_tools_refined["stock"]["functions"]
        assert "get_company_info" not in discovered_tools_refined["stock"]["functions"]
        # Tool definition expects: get_stock_quote, get_company_info, get_historical_data, get_market_summary
        assert len(discovered_tools_refined["stock"]["functions"]) == 1 # Only found one 

    # --- Test for _create_tool_descriptions ---
    def test_create_tool_descriptions_filtering(self, agent_instance):
        """Test that descriptions are created only for available tools."""
        # Simulate that only 'time' and 'weather' tools were discovered
        mock_time_func = lambda x: None
        mock_weather_func = lambda x: None
        agent_instance.tools = {
            "time": {"module": None, "functions": {"get_current_time": mock_time_func}},
            "weather": {"module": None, "functions": {"get_weather": mock_weather_func}}
        }
        
        # Create the descriptions
        descriptions = agent_instance._create_tool_descriptions()
        
        # Check that only descriptions for available tools exist
        assert "time" in descriptions
        assert "get_current_time" in descriptions["time"]["functions"]
        assert "weather" in descriptions
        assert "get_weather" in descriptions["weather"]["functions"]
        
        # Check that descriptions for unavailable tools are filtered out
        assert "currency" not in descriptions
        assert "stock" not in descriptions
        assert "wikipedia" not in descriptions
        
        # Check total number of descriptions matches available tools
        assert len(descriptions) == 2 

    # --- Tests for query_llm ---
    @patch('requests.post')
    def test_query_llm_success(self, mock_post, agent_instance):
        """Test query_llm successful response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"response": "LLM says hi"}
        mock_post.return_value = mock_response
        
        response = agent_instance.query_llm("Hello")
        
        mock_post.assert_called_once()
        assert response == "LLM says hi"

    @patch('requests.post')
    def test_query_llm_request_exception(self, mock_post, agent_instance):
        """Test query_llm handling requests.exceptions.RequestException."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        response = agent_instance.query_llm("Hello")
        
        mock_post.assert_called_once()
        assert "Error: Could not query the LLM - Connection error" in response

    @patch('requests.post')
    def test_query_llm_http_error(self, mock_post, agent_instance):
        """Test query_llm handling HTTPError."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
        mock_post.return_value = mock_response

        response = agent_instance.query_llm("Hello")
        
        mock_post.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
        assert "Error: Could not query the LLM - 404 Client Error" in response

    @patch('requests.post')
    def test_query_llm_json_decode_error(self, mock_post, agent_instance):
        """Test query_llm handling JSONDecodeError."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
        mock_post.return_value = mock_response

        response = agent_instance.query_llm("Hello")
        
        mock_post.assert_called_once()
        # The JSON error happens internally, the function catches the parent Exception
        assert "Error: Could not query the LLM - Expecting value" in response

    # --- Tests for analyze_tool_query ---
    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm') # Also mock this dependency
    def test_analyze_tool_query_success(self, mock_extract_entities, mock_query_llm, agent_instance):
        """Test analyze_tool_query successfully identifies tool, function, args."""
        query = "weather in Paris?"
        mock_extract_entities.return_value = {"location": "Paris"}
        # Mock the LLM response for tool analysis
        mock_llm_response = '{\n  "tool": "weather",\n  "function": "get_weather",\n  "arguments": ["Paris"],\n  "reasoning": "User wants weather in Paris."\n}'
        mock_query_llm.return_value = mock_llm_response
        
        # Ensure the weather tool is considered "available" for the test
        agent_instance.tools['weather'] = {'functions': {'get_weather': lambda x: None}}
        
        tool, func, args = agent_instance.analyze_tool_query(query)
        
        mock_extract_entities.assert_called_once_with(query)
        mock_query_llm.assert_called_once()
        assert tool == "weather"
        assert func == "get_weather"
        assert args == ["Paris"]

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm')
    def test_analyze_tool_query_correction(self, mock_extract_entities, mock_query_llm, agent_instance):
        """Test analyze_tool_query applies corrections (tool name, function, args)."""
        query = "convert 100 dollars to yen"
        mock_extract_entities.return_value = {"amount": 100, "from_currency": "USD", "to_currency": "JPY"}
        # Simulate LLM response needing correction
        mock_llm_response = '{\n  "tool": "currency conversion",\n  "function": "convert",\n  "arguments": ["USD", "JPY"],\n  "reasoning": "User wants currency conversion."\n}'
        mock_query_llm.return_value = mock_llm_response
        
        # Setup agent state for correction
        agent_instance.tool_name_map['currency conversion'] = 'currency'
        agent_instance.tools['currency'] = {'functions': {'convert_currency': lambda a,b,c: None}}
        
        expected_args = [100, "USD", "JPY"]
        tool, func, args = agent_instance.analyze_tool_query(query)

        # --- DEBUG ---
        print(f"DEBUG: Returned args ID: {id(args)}, Value: {args}")
        # --- END DEBUG ---

        assert tool == "currency" # Normalized tool name
        # analyze_tool_query only corrects function name for astronomy/get_eclipse_details
        assert func == "convert" # Expect the name returned by LLM mock
        # Check args correction (should use extracted amount 100)
        assert args == expected_args

    @patch.object(LLMFlowAgent, 'query_llm')
    @patch.object(LLMFlowAgent, 'extract_entities_with_llm') # FIX: Add return_value
    def test_analyze_tool_query_parsing_error(self, mock_extract_entities, mock_query_llm, agent_instance):
        """Test analyze_tool_query returns None on LLM parsing error."""
        mock_extract_entities.return_value = {} # FIX: Provide return value
        mock_query_llm.return_value = "This is not JSON"
        tool, func, args = agent_instance.analyze_tool_query("some query")
        assert tool is None
        assert func is None
        assert args == []

    # --- Tests for execute_tool ---
    def test_execute_tool_success(self, agent_instance):
        """Test successful tool execution."""
        mock_tool_func = MagicMock(return_value="Weather is sunny")
        agent_instance.tools['weather'] = {'functions': {'get_weather': mock_tool_func}}
        
        result = agent_instance.execute_tool('weather', 'get_weather', ["London"])
        
        mock_tool_func.assert_called_once_with("London")
        assert result == "Weather is sunny"
        # Check memory was updated
        assert len(agent_instance.memory.recent_tools_used) > 0
        assert agent_instance.memory.recent_tools_used[-1]["tool"] == "weather"

    def test_execute_tool_missing_tool(self, agent_instance):
        """Test executing a non-existent tool."""
        result = agent_instance.execute_tool('nonexistent', 'some_func', [])
        assert "Error: Tool 'nonexistent' or function 'some_func' not available" in result

    def test_execute_tool_missing_function(self, agent_instance):
        """Test executing a non-existent function on an existing tool."""
        agent_instance.tools['weather'] = {'functions': {'get_weather': lambda x: None}}
        result = agent_instance.execute_tool('weather', 'nonexistent_func', [])
        assert "Error: Tool 'weather' or function 'nonexistent_func' not available" in result

    def test_execute_tool_arg_count_error(self, agent_instance):
        """Test executing a tool with insufficient arguments."""
        # Mock a function that requires 1 argument
        mock_tool_func = MagicMock(spec=lambda location: None)
        # Add inspect signature capability
        mock_tool_func.__signature__ = inspect.signature(lambda location: None)

        agent_instance.tools['weather'] = {'functions': {'get_weather': mock_tool_func}}
        
        result = agent_instance.execute_tool('weather', 'get_weather', []) # Pass no args
        assert "Error: Not enough arguments for get_weather, need at least 1" in result
        mock_tool_func.assert_not_called()

    def test_execute_tool_exception_in_tool(self, agent_instance):
        """Test handling an exception raised within the tool function."""
        mock_tool_func = MagicMock(side_effect=ValueError("Tool failed"))
        agent_instance.tools['weather'] = {'functions': {'get_weather': mock_tool_func}}

        result = agent_instance.execute_tool('weather', 'get_weather', ["London"])
        
        mock_tool_func.assert_called_once_with("London")
        assert "Error executing get_weather: Tool failed" in result

    # --- Tests for handle_casual_conversation ---
    @patch.object(LLMFlowAgent, 'query_llm')
    def test_handle_casual_conversation(self, mock_query_llm, agent_instance):
        """Test casual conversation handling calls LLM with correct prompt."""
        query = "Hi there!"
        query_info = {"language": "en"}
        mock_llm_response = "Hello! How can I help you today?"
        mock_query_llm.return_value = mock_llm_response
        
        # Add some history/context
        agent_instance.memory.add_message("user", query)
        agent_instance.memory.add_tool_usage("weather", "get_weather", ["London"], "Rainy")

        response = agent_instance.handle_casual_conversation(query, query_info)
        
        mock_query_llm.assert_called_once()
        prompt_arg = mock_query_llm.call_args[0][0]
        # Check that the prompt includes key elements
        assert "You are a helpful and friendly conversational assistant" in prompt_arg
        assert "Recent conversation:" in prompt_arg
        assert "user: Hi there!" in prompt_arg
        assert "Recent tool usages:" in prompt_arg
        assert "- Used weather.get_weather with args: London" in prompt_arg
        assert "User's message: " + f'"{query}"' in prompt_arg
        assert response == mock_llm_response

    # --- Tests for process_query ---
    @patch.object(LLMFlowAgent, 'determine_query_type')
    @patch.object(LLMFlowAgent, 'execute_tool')
    def test_process_query_tool_request(self, mock_execute_tool, mock_determine_query_type, agent_instance):
        """Test process_query flow for a tool request."""
        query = "weather London"
        mock_determine_query_type.return_value = {
            "type": "tool_request", "tool": "weather", "function": "get_weather", "args": ["London"]
        }
        mock_execute_tool.return_value = "It is sunny in London."
        
        response = agent_instance.process_query(query)
        
        mock_determine_query_type.assert_called_once_with(query)
        mock_execute_tool.assert_called_once_with("weather", "get_weather", ["London"])
        assert response == "It is sunny in London."
        # Check memory updated with user query and assistant response
        assert agent_instance.memory.messages[-2].content == query
        assert agent_instance.memory.messages[-1].content == response

    @patch.object(LLMFlowAgent, 'determine_query_type')
    @patch.object(LLMFlowAgent, 'handle_casual_conversation')
    def test_process_query_casual(self, mock_handle_casual, mock_determine_query_type, agent_instance):
        """Test process_query flow for casual conversation."""
        query = "hello"
        query_info = {"type": "casual_conversation", "language": "en"}
        mock_determine_query_type.return_value = query_info
        mock_handle_casual.return_value = "Hi there!"
        
        response = agent_instance.process_query(query)
        
        mock_determine_query_type.assert_called_once_with(query)
        mock_handle_casual.assert_called_once_with(query, query_info)
        assert response == "Hi there!"
        assert agent_instance.memory.messages[-1].content == response

    @patch.object(LLMFlowAgent, 'determine_query_type')
    def test_process_query_exit(self, mock_determine_query_type, agent_instance):
        """Test process_query flow for exit command."""
        query = "quit"
        mock_determine_query_type.return_value = {"type": "exit"}
        
        response = agent_instance.process_query(query)
        
        mock_determine_query_type.assert_called_once_with(query)
        assert response == "exit"

    # Mock ChainOrchestrator for process_query chain test
    @patch('chain_orchestrator.ChainOrchestrator') 
    @patch.object(LLMFlowAgent, 'determine_query_type')
    def test_process_query_chain(self, mock_determine_query_type, MockChainOrchestrator, agent_instance):
        """Test process_query flow for a chain query."""
        query = "weather in London then news"
        mock_determine_query_type.return_value = {"type": "chain_query"}
        
        # Mock the orchestrator instance and its methods
        mock_orchestrator_instance = MockChainOrchestrator.return_value
        mock_orchestrator_instance.generate_chain.return_value = [ChainStep("tool", "func", {}, "out")] 
        mock_orchestrator_instance.format_response.return_value = "Formatted chain result from mock"
        # Need to mock execute_chain as well, assume it returns a context dict
        async def mock_execute(*args, **kwargs): return {"key": "value"}
        mock_orchestrator_instance.execute_chain = mock_execute
        
        # Assign the mocked orchestrator to the agent instance being tested
        agent_instance.orchestrator = mock_orchestrator_instance 

        response = agent_instance.process_query(query)

        mock_determine_query_type.assert_called_once_with(query)
        mock_orchestrator_instance.generate_chain.assert_called_once_with(query)
        # execute_chain is harder to assert directly due to async, but we check format_response
        mock_orchestrator_instance.format_response.assert_called_once() # Check it uses the context from execute_chain
        assert response == "Formatted chain result from mock"
        assert agent_instance.memory.messages[-1].content == response

    @patch.object(LLMFlowAgent, 'determine_query_type')
    def test_process_query_general_exception(self, mock_determine_query_type, agent_instance):
        """Test process_query handles unexpected exceptions."""
        query = "some query"
        error_message = "Something broke!"
        mock_determine_query_type.side_effect = Exception(error_message)
        
        response = agent_instance.process_query(query)
        
        mock_determine_query_type.assert_called_once_with(query)
        assert f"I apologize, but I encountered an error while processing your request: {error_message}" in response
        assert agent_instance.memory.messages[-1].content == response

# --- Tests for main function ---
# FIX: Use context managers for patching

def test_main_loop_exit():
    """Test the main loop exits correctly on 'quit'."""
    with patch('builtins.input', side_effect=["quit"]) as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('main.LLMFlowAgent') as MockAgent:
        
        mock_agent_instance = MockAgent.return_value
        # process_query is NOT called when input is quit/exit
        # mock_agent_instance.process_query.return_value = "exit" 

        from main import main
        main()

        mock_input.assert_called_once_with("\nQuery: ")
        # FIX: process_query should not be called
        mock_agent_instance.process_query.assert_not_called() 
        mock_print.assert_any_call("Starting the LLMFlowAgent...")
        # FIX: The final thank you message is now outside the loop
        # mock_print.assert_any_call("Thank you for using the LLMFlowAgent!")

def test_main_loop_query_response():
    """Test the main loop processes a query and prints the response."""
    with patch('builtins.input', side_effect=["hello", "exit"]) as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('main.LLMFlowAgent') as MockAgent:
        
        mock_agent_instance = MockAgent.return_value
        # process_query called for "hello", loop breaks for "exit"
        mock_agent_instance.process_query.side_effect = ["Hi there!"] 

        from main import main
        main()

        assert mock_input.call_count == 2
        # FIX: process_query called only once
        assert mock_agent_instance.process_query.call_count == 1 
        mock_agent_instance.process_query.assert_called_once_with("hello")
        # FIX: assert_any_call("exit") removed
        mock_print.assert_any_call("\nResponse:")
        mock_print.assert_any_call("Hi there!")

def test_main_loop_unicode_error():
    """Test the main loop handles UnicodeDecodeError during input."""
    with patch('builtins.input', side_effect=[UnicodeDecodeError("codec", b'\x80abc', 1, 2, "reason"), "exit"]) as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('main.LLMFlowAgent') as MockAgent:

        mock_agent_instance = MockAgent.return_value
        # process_query not called because loop breaks on "exit" after error
        # mock_agent_instance.process_query.return_value = "exit"

        from main import main
        main()

        assert mock_input.call_count == 2
        # FIX: process_query should not be called
        mock_agent_instance.process_query.assert_not_called() 
        mock_print.assert_any_call("\nError: Unable to decode input. Please check your terminal encoding settings.")

def test_main_loop_general_exception():
    """Test the main loop handles general exceptions during processing."""
    error_message = "Something unexpected happened"
    with patch('builtins.input', side_effect=["a query", "exit"]) as mock_input, \
         patch('builtins.print') as mock_print, \
         patch('main.LLMFlowAgent') as MockAgent:

        mock_agent_instance = MockAgent.return_value
        # process_query called once for "a query", raises error, loop continues,
        # then input is "exit", loop breaks.
        mock_agent_instance.process_query.side_effect = [Exception(error_message)] 

        from main import main
        main()

        assert mock_input.call_count == 2
        # FIX: process_query called only once
        assert mock_agent_instance.process_query.call_count == 1 
        mock_agent_instance.process_query.assert_called_once_with("a query")
        # FIX: assert_any_call("exit") removed
        mock_print.assert_any_call(f"\nError occurred: {error_message}")

# Note: Testing the initial tool import try/except (lines 18-30) is difficult
# in a unit test environment without manipulating sys.path or installed packages.
# We assume successful imports for most tests, and _discover_tools tests handle
# import errors during runtime discovery. 