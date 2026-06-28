
<div align="center">

# OmniClaw 🤖

### Local-First Personal AI Assistant with Multi-Agent Architecture

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

*A Telegram & CLI-powered AI assistant that routes messages to specialized agents, remembers conversations, and runs completely locally.*

---

</div>

## ✨ What It Does

| Feature | Description |
|:---:|:---|
| 🧠 **Smart Routing** | Understands your message and routes it to the right agent automatically |
| 💾 **Persistent Memory** | Remembers your conversations across sessions |
| 🔍 **Web Search** | Searches the web for real-time information |
| 📝 **Note Taking** | Saves notes and reports as markdown files |
| 🏠 **Local-First** | Runs fully local — zero API cost using Ollama |
| 🔧 **MCP Support** | Model Context Protocol server integration |

---

## 🏗️ Architecture

<div align="center">

<img width="1786" height="811" alt="OmniClaw Architecture" src="https://github.com/user-attachments/assets/668eeb32-386f-434e-b8cb-a5a649d69ea7" />

</div>

### System Layers

| Layer | Component | Responsibility |
|:---:|:---|:---|
| **UI** | Telegram Bot, CLI | User interface and commands |
| **API** | FastAPI Gateway | Auth, validation, logging, routing |
| **Agent** | Orchestrator | Decides which agent handles the request |
| **Agents** | Research, Writer, Chat | Execute specific tasks |
| **Tools** | Web Search, File Writer, Gmail | Actual work execution |
| **LLM** | Ollama (local) | Language model inference |
| **Memory** | Supabase | Persistent conversation history per user |
| **MCP** | Registry + Servers | Tool context protocol integration |
| **Infra** | Docker | Containerized, one-command setup |

---

## 🛠️ Tech Stack

| Category | Technology |
|:---|:---|
| **Language** | Python 3.11+ |
| **Bot Framework** | python-telegram-bot |
| **Backend** | FastAPI |
| **LLM** | Ollama (llama3.2:1b) |
| **Agent Framework** | LangChain |
| **Memory** | Supabase (PostgreSQL) |
| **Search** | DuckDuckGo (ddgs) |
| **Infrastructure** | Docker + Docker Compose |

---

## 📦 Project Structure

```
omniclaw/
├── app/                    # Application layer
│   ├── bot/               # Bot interfaces
│   │   ├── telegram_bot.py
│   │   ├── slack_bot.py
│   │   └── notifier.py
│   ├── cli/               # CLI interface
│   │   └── main.py
│   └── web/               # FastAPI gateway
│       └── app.py
├── engine/                # Core AI engine
│   ├── agent/             # Agent orchestration
│   │   └── orchestrator.py
│   ├── llm/              # LLM client
│   │   └── client.py
│   └── memory/           # Memory store
│       └── store.py
├── infra/                # Infrastructure
│   └── mcp/              # MCP servers
│       ├── registry.py
│       └── password_server.py
├── toolkit/              # Tool implementations
│   ├── web_search.py
│   ├── file_writer.py
│   ├── gmail_tool.py
│   ├── research_tool.py
│   ├── writer_tool.py
│   └── tts.py
├── config/              # Configuration files
├── storage/             # Persistent storage
├── tests/               # Test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) installed and running
- [Supabase](https://supabase.com/) account (free tier)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Quick Setup

#### 1. Clone the repository

```bash
git clone https://github.com/TechyLakshay/OmniClaw.git
cd OmniClaw
```

#### 2. Set up Supabase

Run this in your Supabase SQL Editor:

```sql
CREATE TABLE conversations (
    id BIGSERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

#### 3. Create environment file as credential store


Create a `.env` file in the root directory:

```env
TELEGRAM_TOKEN=your_telegram_bot_token
OLLAMA_BASE_URL=http://host.docker.internal:11434
MODEL_NAME=llama3.2:1b
SECRET_KEY=your_secret_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### 4. Pull Ollama model

```bash
ollama pull llama3.2:1b
```

#### 5. Run with Docker

```bash
docker compose up --build
```

---

## 💬 Usage Examples

| Message | What Happens |
|:---|:---|
| `What is the latest news about AI?` | Research Agent searches the web |
| `Save a note about my meeting tomorrow` | Writer Agent saves a markdown file |
| `What is 2 + 2?` | Direct chat response |
| `/start` | Bot introduction |
| `/clear` | Clears your conversation history |

---

## 🎯 Key Features

### Multi-Agent System
- **Orchestrator Agent** — JSON-based routing with scalable registry pattern
- **Research Agent** — DuckDuckGo web search with LLM summarization
- **Writer Agent** — Formats and saves content as markdown files
- **Chat Agent** — Handles general conversation

### Infrastructure
- **AI Gateway** — FastAPI with auth, rate limiting, structured logging
- **Persistent Memory** — Per-user conversation history in Supabase
- **MCP Integration** — Model Context Protocol server support
- **Telegram CLI** — Chat with the model using terminal

### Interfaces
- **Telegram Bot** — Full bot with commands and persistent chat
- **CLI** — Command-line interface for direct interaction
- **Web API** — RESTful gateway for integrations

---

## 🗺️ Roadmap

- [ ] Typing indicator + streaming responses
- [ ] Multimodal — image analysis (LLaVA) + voice input (Whisper)
- [ ] ChannelAdapter pattern — plug in Slack, Discord
- [ ] Proper ReAct loop — think → tool → observe → repeat
- [ ] GitHub tool integration
- [ ] Google Calendar tool
- [ ] `config/settings.py` — Pydantic BaseSettings
- [ ] Vector DB (ChromaDB) for smarter memory

---

## 🎨 Design Decisions

| Decision | Rationale |
|:---|:---|
| **Ollama** | Local inference — zero API cost during development. Swap to Gemini/GPT-4 via LiteLLM when needed. |
| **Supabase** | Persistent memory across sessions without managing a local DB. Free tier is sufficient. |
| **Agent Registry** | Adding a new agent is one line in the dict. Nothing else changes. |
| **Manual JSON parsing** | Ollama local models are unreliable with structured output. Manual `json.loads` with fallback is more stable. |
| **MCP Support** | Standardized tool integration for better context awareness. |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

*Built with ❤️ by [Lakshay](https://github.com/TechyLakshay)*

*Intern, Python Developer, Agentic AI Enthusiast*

</div>
