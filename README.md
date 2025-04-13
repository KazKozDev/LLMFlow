<p align="center">
  <img src="https://github.com/user-attachments/assets/906ba435-47eb-42e2-be75-7dc971875b42" alt="logo"/>
</p>

# LLMFlowAgent - Tool-Using Conversational Agent

A LLM agent that understands natural language and connects to real-world data sources.

LLMFlowAgent is a full-fledged AI agent built in Python that combines the power of natural language understanding with access to various real-world data sources and tools. Unlike traditional language models that are limited to their training data, LLMFlowAgent can interact with current information about weather, news, stocks, geolocation, and more—all through natural language conversations. Powered by Ollama with Gemma3:12b (or other compatible models), this agent interprets user requests and autonomously selects the appropriate tools to fulfill tasks.

### Agent Overview

LLMFlowAgent operates as a complete AI agent that can:

-   Understand requests in natural language.
-   Determine which tools are needed to fulfill a request.
-   Access external data sources in real-time via integrated tools.
-   Maintain conversation context using a memory system.
-   Provide coherent, informed responses based on LLM capabilities and tool outputs.
-   Distinguish between casual chat and tool-requiring tasks.

At its core, LLMFlowAgent uses Ollama running the specified model (default: Gemma3:12b) for powerful language understanding and generation capabilities, enabling it to seamlessly bridge the gap between natural language requests and specialized data tools.

### Key Capabilities

-   🧠 **Advanced Natural Language Understanding** - Comprehends complex requests and context via the LLM.
-   🧩 **Intelligent Tool Selection** - Automatically chooses which tools to use based on the request.
-   🌐 **Real-time Data Access** - Connects to current information using specialized tools.
-   🗣️ **Contextual Conversation** - Maintains context throughout conversations using a dedicated memory system.
-   🛡️ **Fallback Mechanisms** - Some tools include basic fallback mechanisms or error handling.
-   🔌 **Extensible Architecture** - Easily add new tools by creating Python modules in the `tools/` directory.
-   🌍 **Basic Multi-language Awareness** - Attempts to detect query language.
-   ⚙️ **Built-in Safeguards** - Some tools incorporate basic rate limiting or retry logic.

### Integrated Tools

LLMFlowAgent has access to the following specialized tools (located in the `tools/` directory):

-   💨 **Air Quality Tool** (`air_quality_tool.py`) - Air quality information for locations worldwide.
-   💱 **Currency Tool** (`currency_tool.py`) - Real-time currency conversion rates.
-   🗺️ **Geolocation Tool** (`geolocation_tool.py`) - Geographic information and location services.
-   📰 **News Tool** (`news_tool.py`) - Latest news articles from various sources via RSS.
-   📈 **Stock Tool** (`stock_tool.py`) - Stock market data and financial information (may use fallback data due to free tier limitations).
-   🕒 **Time Tool** (`time_tool.py`) - Time zone conversions and management.
-   🌐 **Web Parser Tool** (`web_parser_tool.py`) - Extract content from webpages.
-   🌡️ **Weather Tool** (`weather_tool.py`) - Current weather conditions and forecasts worldwide.
-   📚 **Wikipedia Tool** (`wikipedia_tool.py`) - Access information from Wikipedia.
-   🔍 **Search Tool** (`search_tool.py`) - Web search capabilities using DuckDuckGo.

## Technical Architecture

LLMFlowAgent is built with a modular Python architecture:

-   **Agent Core (`LLMFlowAgent` class)**: Handles interaction with Ollama (for NLU, query classification, tool selection), manages tool discovery and execution, and orchestrates the conversation flow.
-   **Memory System (`ConversationMemory` class)**: Maintains conversation history, user context (basic), and recent tool usage.
-   **Tool Modules (in `tools/`)**: Individual Python files, each containing functions for a specific capability (e.g., weather, stocks). The agent dynamically discovers and loads these.
-   **Command-Line Interface (`main.py`)**: Provides a simple text-based interface for interacting with the agent.

### Prerequisites

-   **Python:** Python 3.8 or higher is recommended.
-   **Ollama:** You need Ollama installed and running. The agent is configured by default to connect to `http://localhost:11434`.
    -   Ensure you have a suitable model pulled (e.g., `ollama pull gemma3:12b`). The default model used is `gemma3:12b` but can be changed in `main.py`.
-   **pip:** Python package installer.

### Installation

```bash
# Clone the repository
git clone https://github.com/KazKozDev/LLMFlow.git
cd LLMFlow

# Create a virtual environment (recommended)
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Download NLTK data (required by the News/Web Parser tools)
python -m nltk.downloader punkt

# Verify Ollama is running and the model is available
ollama list
```

### Basic Usage

Run the main script from the project's root directory:

```bash
python main.py
```

The agent will initialize and present a Query: prompt. Enter your requests or chat naturally.

Example CLI Interaction:

```
Starting the LLMFlowAgent...
All tools imported successfully
Agent started with 10 available tools

You can make queries such as:
- 'What's the weather in Madrid?'
[...]
- Or simply chat with me like 'Hello, how are you?'

Type 'exit' or 'quit' to end.

Query: What is the price of NVIDIA stock and the weather in London?

Response:
Using tool: stock, function: get_stock_quote, args: ['NVIDIA']
Current Quote for NVIDIA Corporation (NVDA):

Price: 120.89 USD (+1.37 (+1.15%))
The stock is up today.

Day Range: 119.68 - 123.31 USD
Volume: 154.32M
Market Cap: $2.97T
P/E Ratio: 71.11
Dividend Yield: 0.03%
52-Week Range: 39.23 - 140.76 USD
Exchange: NASDAQ
Status: Market Closed

Data source: Yahoo Finance, as of 2024-07-26 19:59:59


Query: And the weather in London?

Response:
Using tool: weather, function: get_weather, args: ['London']
Current weather in London, United Kingdom: Partly cloudy. Temperature is 21.0°C, feels like 20.5°C. Humidity is 70%. Wind speed is 13.3 km/h.

Query: exit
Thank you for using the LLMFlowAgent!
```

### Configuration

- **Ollama URL**: The Ollama API endpoint is set in main.py within the LLMFlowAgent class constructor (ollama_url). Default is http://localhost:11434.
- **LLM Model**: The specific Ollama model is set in main.py (self.model). Default is gemma3:12b. Change this to match a model you have available in Ollama.
- **Conversation Memory**: The maximum number of messages stored in memory can be adjusted in the ConversationMemory class (max_messages, default 10).

### How it Works

1. The user enters a query via the CLI.
2. The LLMFlowAgent adds the query to the ConversationMemory.
3. The agent uses the LLM (determine_query_type) to classify the query as either tool_request or casual_conversation, considering the conversation history.
4. If tool_request:
   - The agent uses the LLM again (analyze_tool_query) to determine the appropriate tool, function, and arguments based on the available tool descriptions.
   - The execute_tool method calls the corresponding function from the tool module.
   - The result from the tool is returned as the response.
5. If casual_conversation:
   - The agent uses the LLM (handle_casual_conversation) to generate a conversational response, using the conversation history and context.
   - The LLM's generated text is returned as the response.
6. The agent adds its response to the ConversationMemory.
7. The response is printed to the user.

### License

This project is licensed under the MIT License - see the LICENSE file for details.

If you like this project, please give it a star ⭐

For questions, feedback, or support, reach out to:
Artem KK | MIT LICENSE