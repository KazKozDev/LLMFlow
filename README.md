<p align="center">
  <img src="https://github.com/user-attachments/assets/906ba435-47eb-42e2-be75-7dc971875b42" alt="logo" height="210"/>
  <br><br>
  <img src="https://img.shields.io/badge/python-3.9%2B-green" alt="Python">
  <img src="https://img.shields.io/badge/Type-Agentic%20AI-blue" alt="Type">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success" alt="Status">
  <br><br>
  <b>LLMFlowAgent: An Intelligent Agent with Tool Integration</b>
</p>

**LLMFlowAgent** is a **production-ready Agentic AI** system built in Python, seamlessly connecting large language models (LLMs) to real-world data sources. Powered by **Ollama** with the **Gemma3:12b** model (or compatible LLMs), it leverages advanced reasoning chains to process natural language queries, orchestrate specialized tools, and deliver accurate, context-aware responses. Whether handling casual conversations or complex tasks like fetching weather, news, or web search results, LLMFlowAgent is designed for reliability, extensibility, and enterprise-grade performance.

### Features

- **Advanced Reasoning**: Sophisticated decision-making algorithms classify queries and select optimal tools.
- **Tool Integration**: Modular ecosystem of tools for tasks like weather, news aggregation, and web searches.
- **Real-Time Data Access**: Connects to free APIs (Open-Meteo, DuckDuckGo, RSS feeds) for up-to-date info.
- **Conversation Memory**: Maintains context with an optimized memory system for natural dialogues.
- **Multilingual Support**: Processes queries in multiple languages with entity normalization.
- **Extensible Architecture**: Easily add new tools or integrate with other LLMs via a modular design.
- **Local Deployment**: Runs locally with Ollama, ensuring privacy and data control.

### Supported Tools

| Tool Name            | Description                                      | File                                    |
|----------------------|--------------------------------------------------|-----------------------------------------|
| Air Quality Tool     | Retrieves air quality data for locations         | [air_quality_tool.py](tools/air_quality_tool.py) |
| Astronomy Tool       | Provides celestial events and planet info        | [astronomy_tool.py](tools/astronomy_tool.py) |
| Currency Tool        | Converts currencies with real-time rates         | [currency_tool.py](tools/currency_tool.py) |
| Geolocation Tool     | Offers location data and distance calculations   | [geolocation_tool.py](tools/geolocation_tool.py) |
| News Tool            | Aggregates news via RSS feeds                    | [news_tool.py](tools/news_tool.py) |
| Stock Tool           | Delivers financial market data                   | [stock_tool.py](tools/stock_tool.py) |
| Time Tool            | Handles time zone conversions                    | [time_tool.py](tools/time_tool.py) |
| Weather Tool         | Provides weather forecasts and conditions        | [weather_tool.py](tools/weather_tool.py) |
| Wikipedia Tool       | Fetches reference information from Wikipedia     | [wikipedia_tool.py](tools/wikipedia_tool.py) |
| Web Parser Tool      | Extracts content from web pages                  | [web_parser_tool.py](tools/web_parser_tool.py) |
| Search Tool          | Performs web searches via DuckDuckGo             | [search_tool.py](tools/search_tool.py) |

---

### Project Classification

1. **AI Assistant with Tool Integration**:
   - Combines LLM capabilities with external tools for complex tasks.
   - **Similar to**: LangChain, AutoGPT, OpenAI Assistants API, with enhanced modularity and local deployment.

2. **Action Chain Orchestrator**:
   - Manages sequences of tool calls for multi-step tasks.
   - **Applications**: Enterprise automation, API-driven workflows, data aggregation.

3. **Extensible Tool Platform**:
   - Modular design for seamless addition of new tools.
   - **Similar to**: Hugging Face Agents, CrewAI.

4. **Agentic AI System**:
   - Built on autonomous AI research with multi-step reasoning and tool synergy.
   - **Use Cases**: Research, prototyping, production-grade AI solutions.

---

### Technical Architecture

- **Agent Core**: Manages LLM interactions, query classification, and tool execution via `main.py`.
- **Memory System**: Handles conversation history with the `ConversationMemory` for context-aware responses.
- **Tool Modules**: Independent Python modules for specialized tasks, dynamically discovered.
- **CLI Interface**: Professional-grade command-line interface for interactive testing.
- **LLM Backend**: Integrates with Ollama (default: `gemma3:12b`) for local, privacy-focused processing.
- **Data Sources**: Uses free APIs (Open-Meteo, DuckDuckGo, RSS) with caching for performance.

---

### Prerequisites
- **Python**: 3.9 or higher
- **Ollama**: Installed and running locally with the `gemma3:12b` model (or compatible)
- **NLTK Data**: Required for News and Web Parser tools

### Steps

```bash
# Clone the repository
git clone https://github.com/KazKozDev/LLMFlow.git
cd LLMFlow

# Create and activate a virtual environment (recommended)
python -m venv venv
# On Windows: venv\Scripts\activate
# On macOS/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download NLTK data for News and Web Parser tools
python -m nltk.downloader punkt

# Verify Ollama is running and the model is available
ollama list
```

### Basic Usage

Run the main script from the project root:

```bash
python main.py
```

The agent will initialize and display a Query: prompt. Enter natural language requests, such as:

- "What's the weather in Tokyo?"
- "Show me the latest technology news."
- "Search for recent AI breakthroughs."
- "How are you today?" (for casual conversation)

Type `exit`, `quit`, or `q` to close the agent.

### Example Queries

```
Query: What's the weather in Moscow?
Response: Current weather in Moscow, Russia: Partly cloudy. Temperature is 5.2°C (41.4°F). Wind speed is 3.4 m/s.

Query: Latest news on climate change
Response: Here are 5 news results for 'climate change':
1. Global Warming Reaches New Highs in 2025
   Source: BBC News | Today, 08:15
   Link: https://bbc.com/news/climate-123456
   Rising temperatures spark new concerns...

Query: Hello, how are you?
Response: Hey there! I'm doing great, thanks for asking. Just chilling in the digital realm, ready to answer your questions. What's on your mind?
```

### Configuration

Customize the agent by modifying settings in main.py:

- **Ollama URL**: Set in the LLMFlowAgent constructor (ollama_url). Default: http://localhost:11434.
- **LLM Model**: Configured in LLMFlowAgent (self.model). Default: gemma3:12b. Update to match your model.
- **Conversation Memory**: Adjust the maximum stored messages (max_messages, default: 10).
- **Tool Directory**: Tools are loaded from the tools/ folder. Add new tools by placing modules in the directory.

### How It Works

1. **Query Input**: User submits a query via the CLI.
2. **Memory Update**: Query is added to ConversationMemory for context tracking.
3. **Query Classification**: LLM (determine_query_type) analyzes the query, using history to classify it as:
   - tool_request: Requires a specific tool (e.g., weather, news).
   - chain_query: Needs multiple tools in sequence.
   - casual_conversation: General dialogue.
4. **Tool Execution** (if tool_request):
   - LLM (analyze_tool_query) selects the tool, function, and arguments based on tool descriptions.
   - execute_tool invokes the tool's function (e.g., get_weather).
   - Results are formatted and returned.
5. **Chain Orchestration** (if chain_query):
   - ChainOrchestrator generates and executes a sequence of tool calls.
   - Results are combined into a cohesive response.
6. **Casual Conversation** (if applicable):
   - LLM (handle_casual_conversation) generates a natural response using context and history.
7. **Response Storage**: Agent's response is saved in ConversationMemory.
8. **Output**: Response is displayed to the user.

### Use Cases

- **Chatbots**: Build conversational bots for platforms like Telegram or Discord with real-time data access.
- **Automation**: Automate tasks like news monitoring, weather updates, or currency conversions.
- **Education**: Use as a teaching tool for AI, NLP, or API integration courses.
- **Research**: Collect and analyze data (e.g., news trends, weather patterns) with minimal setup.
- **Local Assistants**: Create privacy-focused, offline AI assistants for personal or enterprise use.
- **Prototyping**: Rapidly develop and test new AI-driven features or tools.

### Contributing

We welcome contributions! To get started:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Add changes or new tools in the tools/ directory.
4. Update documentation and tests as needed.
5. Submit a pull request with a clear description.

### Acknowledgments

- **Ollama**: For a robust local LLM platform.
- **Open-Meteo**: For free weather and geocoding APIs.
- **DuckDuckGo**: For enabling web search functionality.
- **RSS Providers**: For reliable news feeds (BBC, CNN, NYT, and others).
- **Python Community**: For libraries like requests, feedparser, and BeautifulSoup.
---

If you like this project, please give it a star ⭐

For questions, feedback, or support, reach out to:

[Artem KK](https://www.linkedin.com/in/kazkozdev/) | MIT [LICENSE](LICENSE) 
