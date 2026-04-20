from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import HumanMessage, AIMessage
# from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import logging
from pathlib import Path
from langchain_groq import ChatGroq


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


load_dotenv()

CORE_CONTEXT_FILES = [
    "context/IDENTITY.md",
    "context/SOUL.md",
    "context/USER.md"
]


def get_llm():
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        model=os.getenv("MODEL_NAME", "llama3.1")
    )


# -----------------------------
# ✅ Dynamic Prompt Template
# -----------------------------


def load_core_context() -> str:
    root_dir = Path(__file__).resolve().parent.parent
    sections = []

    for filename in CORE_CONTEXT_FILES:
        file_path = root_dir / filename
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8").strip()
        if not content:
            continue

        sections.append(f"[{filename}]\n{content}")

    return "\n\n".join(sections)


def get_prompt_template(system: str):
    return ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])




# -----------------------------
# ✅ History Builder
# -----------------------------
def build_history(history: list) -> list:
    messages = []

    for msg in history:
        content = str(msg.get("content", ""))  # 🔥 force string

        if msg["role"] == "human":
            messages.append(HumanMessage(content=content))
        elif msg["role"] == "ai":
            messages.append(AIMessage(content=content))

    return messages


# -----------------------------
# ✅ LLM Invocation
# -----------------------------
def  invoke_llm(prompt: str, system: str, history: list = None) -> str:
    try:
        if history is None:
            history = []

        llm = get_llm()
        core_context = load_core_context()
        final_system = system if not core_context else f"{core_context}\n\n[Task Prompt]\n{system}"
        prompt_template = get_prompt_template(final_system)

        chain = prompt_template | llm

        response = chain.invoke({
            "history": build_history(history),
            "input": str(prompt)
        })

        return response.content

    except Exception as e:
        return f"Error: {str(e)}"
