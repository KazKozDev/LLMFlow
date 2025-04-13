<p align="center">
  <img src="https://github.com/user-attachments/assets/885f45f2-54d6-45ce-b63f-5fc3a0022cb9" alt="logo"/>
</p>

# LLMFlow

A powerful AI agent that understands natural language and connects to real-world data sources.

LLMFlow is a full-fledged AI agent that combines the power of natural language understanding with access to various real-world data sources and tools. Unlike traditional language models that are limited to their training data, LLMFlow can interact with current information about weather, news, stocks, geolocation, and more—all through natural language conversations. Powered by Ollama with Gemma3:12b, this agent interprets user requests and autonomously selects the appropriate tools to fulfill tasks.

## Agent Overview

LLMFlow operates as a complete AI agent that can:

- Understand requests in natural language
- Determine which tools are needed to fulfill a request
- Access external data sources in real-time
- Process and contextualize information
- Provide coherent, informed responses

At its core, LLMFlow uses Ollama running the Gemma3:12b model for powerful language understanding and generation capabilities, enabling it to seamlessly bridge the gap between natural language requests and specialized data tools.

### Key Capabilities

- 🧠 **Advanced Natural Language Understanding** - Comprehends complex requests and context
- 🔍 **Autonomous Tool Selection** - Automatically chooses which tools to use based on the request
- 🌐 **Real-time Data Access** - Connects to current information across the web
- 🧩 **Contextual Understanding** - Maintains context throughout conversations
- 🔄 **Fallback Mechanisms** - Gracefully handles service unavailability
- 🔌 **Extensible Architecture** - Easily add new tools to expand agent capabilities
- 💡 **Reasoning & Planning** - Breaks down complex tasks into steps
- 🌍 **Multi-language Support** - Works with queries in multiple languages
- 🛡️ **Built-in Safeguards** - Rate limiting and responsible API usage

## Integrated Tools

LLMFlow has access to the following specialized tools:

- **🌡️ Weather Tool** - Current weather conditions and forecasts worldwide
- **💱 Currency Tool** - Real-time currency conversion rates
- **🗺️ Geolocation Tool** - Geographic information and location services
- **📰 News Tool** - Latest news articles from various sources
- **🔍 Search Tool** - Web search capabilities
- **📈 Stock Tool** - Stock market data and financial information
- **🕒 Time Tool** - Time zone conversions and management
- **💨 Air Quality Tool** - Air quality information for locations worldwide
- **🌐 Web Parser Tool** - Extract content from webpages
- **📚 Wikipedia Tool** - Access information from Wikipedia

## Technical Architecture

LLMFlow is built with a modular agent architecture:

- **Agent Core**: Powered by Ollama running Gemma3:12b, handling natural language understanding and decision-making
- **Tool Manager**: Connects the agent to various data tools and handles tool selection
- **Server**: A NodeJS express server that orchestrates the agent and tools
- **Memory System**: Maintains conversation context and remembers previous interactions

## 🚀 Getting Started

### Prerequisites

- Node.js (v14 or above)
- npm or yarn
- Ollama (for running Gemma3:12b locally)

### Installation

```bash
# Clone the repository
git clone https://github.com/KazKozDev/LLMFlow.git
cd LLMFlow

# Install dependencies
yarn install

# Set up Ollama with Gemma3:12b
ollama pull gemma3:12b

# Start the agent
yarn start
```

### Basic Usage

```javascript
// Example: Interacting with the LLMFlow agent
const { LLMFlow } = require('llmflow');

// Initialize the agent
const agent = new LLMFlow({
  model: 'gemma3:12b',
  provider: 'ollama',
  url: 'http://localhost:11434'
});

// Send a query to the agent
const response = await agent.chat("What's the weather in Tokyo and the current USD to JPY exchange rate?");
console.log(response);
// Agent will automatically access weather and currency tools to answer the question
```

### Development

```bash
# Install development dependencies
yarn install:dev

# Run tests
yarn test

# Build for production
yarn build
```

### API Reference

```
POST /api/chat
{
  "message": "What's the current weather in Paris?",
  "conversation_id": "optional-conversation-id"
}

GET /api/tools/weather?location=London
GET /api/tools/currency/convert?amount=100&from=USD&to=EUR
```


### License

This project is licensed under the  file for details.

---
If you like this project, please give it a star ⭐

For questions, feedback, or support, reach out to:

[Artem KK](https://www.linkedin.com/in/kazkozdev/) | MIT [LICENSE](LICENSE)