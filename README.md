<p align="center">
  <img src="https://github.com/user-attachments/assets/906ba435-47eb-42e2-be75-7dc971875b42" alt="logo" height="220"/>
  <br><br>
  <img src="https://img.shields.io/badge/python-3.9%2B-green" alt="Python">
  <img src="https://img.shields.io/badge/Type-Agentic%20AI-blue" alt="Type">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success" alt="Status">
  <br><br>
  <b>An intelligent agent with tool support</b>.
</p>

LLMFlow Agent is an **Agentic AI** system built in Python, connecting language models to real-world data sources. Using Ollama with Gemma3:12b (or compatible models), it implements advanced reasoning chains to process natural language requests and orchestrate appropriate tools to fulfill complex tasks.

**The agent**
* Implements production-level reasoning frameworks
* Executes sophisticated tool selection algorithms
* Accesses external data in real-time with enterprise-grade reliability
* Maintains conversation context through optimized memory systems
* Determines optimal action pathways through proprietary decision trees

<table border="1" cellpadding="8" cellspacing="0">
  <thead>
    <tr>
      <th>Tool Name</th>
      <th>Description</th>
      <th>File</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Air Quality Tool</td>
      <td>Environmental data</td>
      <td><a href="tools/air_quality_tool.py">air_quality_tool.py</a></td>
    </tr>
    <tr>
      <td>Currency Tool</td>
      <td>Exchange rates with banking-grade accuracy</td>
      <td><a href="tools/currency_tool.py">currency_tool.py</a></td>
    </tr>
    <tr>
      <td>Geolocation Tool</td>
      <td>Location services</td>
      <td><a href="tools/geolocation_tool.py">geolocation_tool.py</a></td>
    </tr>
    <tr>
      <td>News Tool</td>
      <td>RSS-based news aggregation</td>
      <td><a href="tools/news_tool.py">news_tool.py</a></td>
    </tr>
    <tr>
      <td>Stock Tool</td>
      <td>Financial data processing</td>
      <td><a href="tools/stock_tool.py">stock_tool.py</a></td>
    </tr>
    <tr>
      <td>Time Tool</td>
      <td>Timezone conversions</td>
      <td><a href="tools/time_tool.py">time_tool.py</a></td>
    </tr>
    <tr>
      <td>Web Parser Tool</td>
      <td>Content extraction</td>
      <td><a href="tools/web_parser_tool.py">web_parser_tool.py</a></td>
    </tr>
    <tr>
      <td>Weather Tool</td>
      <td>Forecasts and conditions</td>
      <td><a href="tools/weather_tool.py">weather_tool.py</a></td>
    </tr>
    <tr>
      <td>Wikipedia Tool</td>
      <td>Reference information</td>
      <td><a href="tools/wikipedia_tool.py">wikipedia_tool.py</a></td>
    </tr>
    <tr>
      <td>Search Tool</td>
      <td>Web search via DuckDuckGo</td>
      <td><a href="tools/search_tool.py">search_tool.py</a></td>
    </tr>
  </tbody>
</table>


### Project Classification
1. **AI-assistant with tool integration**:
   * Implements production-ready LLM capabilities with external tools for complex tasks
   * Similar to: LangChain, AutoGPT, OpenAI Assistants API, but with enhanced reliability

2. **Action Chain Orchestrator**:
   * Engineered for high-performance tool sequence management
   * Applications: enterprise request automation, mission-critical API integration

3. **Extensible Tool Platform**:
   * Industry-standard modular design for scalable tool ecosystems
   * Similar to: Hugging Face Agents, CrewAI

4. **Agentic AI System**:
   * Built on cutting-edge research in autonomous AI agents
   * Implements multi-step reasoning and tool synergy

### Technical Architecture
- **Agent Core**: State-of-the-art Ollama interaction, tool selection and execution
- **Memory System**: Optimized conversation history management
- **Tool Modules**: Independently scalable Python modules for specialized functions
- **CLI**: Professional-grade text interface

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

---

If you like this project, please give it a star ⭐

For questions, feedback, or support, reach out to:

[Artem KK](https://www.linkedin.com/in/kazkozdev/) | MIT [LICENSE](LICENSE)
