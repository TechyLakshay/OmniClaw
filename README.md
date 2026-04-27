
# Mini-Claw 🤖

A local-first personal AI assistant built on Telegram and CLI with a multi-agent architecture, persistent memory, and tool calling. Inspired by the OpenClaw architecture pattern.


> Built from scratch :)
---

## What It Does

- Understands your message and routes it to the right agent automatically
- Remembers your conversations across sessions
- Searches the web for real-time information
- Saves notes and reports as markdown files
- Runs fully local — zero API cost -> used ollama(no cost LLM running locally)
- Now can understand test based on semantics

---

## Architecture


<img width="1786" height="811" alt="Screenshot 2026-04-10 160434" src="https://github.com/user-attachments/assets/668eeb32-386f-434e-b8cb-a5a649d69ea7" />


### Layers

| Layer | Component | Responsibility |
|---|---|---|
| UI | Telegram Bot | User interface, commands |
| Gateway | FastAPI | Auth, validation, logging, routing |
| Agent | Orchestrator | Decides which agent handles the request |
| Agents | Research, Writer, Chat | Execute specific tasks |
| Tools | Web Search, File Writer | Actual work — search, write |
| LLM | Ollama (local) | Language model inference |
| Memory | Supabase | Persistent conversation history per user |
| Infra | Docker | Containerized, one-command setup |

---

## Stack

| | Technology |
|---|---|
| Language | Python 3.11 |
| Bot | python-telegram-bot |
| Backend | FastAPI |
| LLM | Ollama (llama3.2:1b) |
| Agent Framework | LangChain |
| Memory | Supabase (PostgreSQL) |
| Search | DuckDuckGo (ddgs) |
| Infra | Docker + Docker Compose |

---

## Features

- **AI Gateway** — FastAPI with auth, rate limiting, structured logging, request IDs
- **Orchestrator Agent** — JSON-based routing with scalable AGENTS registry pattern
- **Research Agent** — DuckDuckGo web search with LLM summarization
- **Writer Agent** — Formats and saves content as markdown files
- **Persistent Memory** — Per-user conversation history stored in Supabase
- **Telegram Commands** — `/start` for introduction, `/clear` to reset history
- **Docker** — Fully containerized, runs anywhere with one command
- **Telegram CLI** - Chat with Model using Terminal

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/) installed and running
- [Supabase](https://supabase.com/) account (free tier)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### 1. Clone the repo

```bash
git clone https://github.com/your-username/mini-claw
cd mini-claw
```

### 2. Set up Supabase

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

### 3. Create `.env` file

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

### 4. Pull Ollama model

```bash
ollama pull llama3.2:1b
```

### 5. Run

```bash
docker compose up --build
```

---

## Usage

| Message | What Happens |
|---|---|
| `What is the latest news about AI?` | Research Agent searches the web |
| `Save a note about my meeting tomorrow` | Writer Agent saves a markdown file |
| `What is 2 + 2?` | Direct chat response |
| `/start` | Bot introduction |
| `/clear` | Clears your conversation history |

---

## Project Structure

```
mini-claw/
├── bot/
│   └── telegram_bot.py       # Telegram interface, commands
├── gateway/
│   └── app.py                # FastAPI gateway — auth, logging, routing
├── core/
│   └── llm.py                # LLM setup, prompt templates, history builder
├── memory/
│   └── database.py           # Supabase — save, load, clear history
├── agents/
│   ├── orchestrator.py       # Routes to correct agent
│   ├── research_agent.py     # Web search + summarize
│   └── writer_agent.py       # Format + save markdown
├── tools/
│   ├── web_search.py         # DuckDuckGo search tool
│   └── file_writer.py        # Markdown file writer
├── notes/                    # Saved notes output here
├── .env                      # Environment variables (not committed)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Roadmap

- [ ] Typing indicator + streaming responses
- [ ] Multimodal — image analysis (LLaVA) + voice input (Whisper)
- [ ] ChannelAdapter pattern — plug in Slack, Discord
- [ ] Proper ReAct loop — think → tool → observe → repeat
- [ ] GitHub tool integration
- [ ] Google Calendar tool
- [ ] `config/settings.py` — Pydantic BaseSettings
- [ ] Vector DB (ChromaDB) for smarter memory

---

## Key Design Decisions:

**Why Ollama?** Local inference — zero API cost during development. Swap to Gemini/GPT-4 via LiteLLM when needed.

**Why Supabase?** Persistent memory across sessions without managing a local DB. Free tier is sufficient.

**Why AGENTS registry pattern?** Adding a new agent is one line in the dict. Nothing else changes.

**Why manual JSON parsing over `with_structured_output`?** Ollama local models are unreliable with structured output on every call. Manual `json.loads` with fallback is more stable.

---

## License

MIT

---

*Built by Lakshay — intern, Python developer, agentic AI enthusiast.*

