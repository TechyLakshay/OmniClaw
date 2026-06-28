# from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import HumanMessage, AIMessage
# from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging
import time
from pathlib import Path
from anthropic import Anthropic




logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


load_dotenv()

CORE_CONTEXT_FILES = [
    "context/IDENTITY.md",
    "context/SOUL.md",
    "context/USER.md"
]


# def get_llm():
#     return ChatOllama(
#         base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
#         model=os.getenv("MODEL_NAME", "llama3.1")
#     )
# def get_llm(
#     model: str = "qwen/qwen2.5-72b-instruct",
#     temperature: float = 0.7,
#     max_tokens: int = 1024,
#     api_key: str = None
# ):
#     """Get OpenRouter LLM instance via ChatOpenAI compatible interface."""
#     if api_key is None:
#         api_key = os.getenv("OPENROUTER_API_KEY")
    
#     if not api_key:
#         raise ValueError("OPENROUTER_API_KEY not set in environment")
    
#     return ChatOpenAI(
#         base_url="https://openrouter.ai/api/v1",
#         api_key=api_key,
#         model=model,
#         temperature=temperature,
#         max_tokens=max_tokens,
#         timeout=60,
#     )

# Update core/llm.py get_llm() function
# def get_llm(
#     model: str = "qwen2.5:7b",
#     temperature: float = 0.7,
# ):
#     start_time = time.perf_counter()
#     logger.info(f"llm:get_llm:start model={model} temperature={temperature}")

#     if "/" in model:
#         raise ValueError(f"Invalid local model name: {model}")

#     llm = ChatOllama(
#         base_url="http://localhost:11434",
#         model=model,
#         temperature=temperature,
#     )
#     logger.info(f"llm:get_llm:ready elapsed={time.perf_counter() - start_time:.2f}s model={model}")
#     return llm

client = Anthropic(api_key="55b0360aa23441a99cf6ba1985093128.DkWnAWzRUELQXRTm",
                   base_url="https://api.z.ai/api/anthropic")

def get_llm(
    model: str = "claude-haiku-4-5",
    temperature: float = 0.7,
    max_tokens: int = 1024,
):
    """Get Anthropic LLM instance using direct client (LangChain-compatible interface)."""
    return {
        "client": client,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def get_prompt_template(system: str):
    """Create a LangChain prompt template for compatibility."""
    return ChatPromptTemplate.from_messages([
        ("system", system),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])


# -----------------------------
# ✅ Dynamic Prompt Template
# -----------------------------


def load_core_context() -> str:
    """
    load the context models which is used by the LLM
    to identify all the workings, behaviour and other
    context and strictly work according to them.
    
    """
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




# -----------------------------
# ✅ History Builder
# -----------------------------
def build_history(history: list) -> list:
    """Build conversation history in LangChain format."""
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
def invoke_llm(prompt: str, system: str, history: list = None) -> str:
    """
    Invoke the LLM with proper history and system context using Anthropic API.

    Args:
        prompt: User message
        system: System prompt/instructions
        history: Conversation history (list of dicts with 'role' and 'content')

    Returns:
        LLM response as string
    """
    try:
        total_start = time.perf_counter()
        logger.info(
            f"llm:invoke:start prompt_len={len(str(prompt))} system_len={len(str(system))} "
            f"history_len={len(history) if history else 0}"
        )

        if history is None:
            history = []

        llm_start = time.perf_counter()
        llm_config = get_llm()
        client = llm_config["client"]
        logger.info(f"llm:invoke:client_ready elapsed={time.perf_counter() - llm_start:.2f}s")

        context_start = time.perf_counter()
        core_context = load_core_context()
        final_system = system if not core_context else f"{core_context}\n\n[Task Prompt]\n{system}"
        logger.info(
            f"llm:invoke:prompt_ready elapsed={time.perf_counter() - context_start:.2f}s "
            f"final_system_len={len(final_system)}"
        )

        # Build messages for Anthropic API (convert from dict format)
        anthropic_messages = []
        for msg in history:
            content = str(msg.get("content", ""))
            if msg["role"] == "human":
                anthropic_messages.append({"role": "user", "content": content})
            elif msg["role"] == "ai":
                anthropic_messages.append({"role": "assistant", "content": content})
        anthropic_messages.append({"role": "user", "content": str(prompt)})

        invoke_start = time.perf_counter()
        logger.info("llm:invoke:model_call:start")

        response = client.messages.create(
            model=llm_config["model"],
            temperature=llm_config["temperature"],
            max_tokens=llm_config["max_tokens"],
            system=final_system,
            messages=anthropic_messages
        )

        logger.info(
            f"llm:invoke:model_call:done elapsed={time.perf_counter() - invoke_start:.2f}s"
        )

        total_elapsed = time.perf_counter() - total_start
        response_content = response.content[0].text
        logger.info(
            f"llm:invoke:success total_elapsed={total_elapsed:.2f}s response_len={len(response_content)}"
        )

        return response_content

    except Exception as e:
        logger.error(f"LLM invocation error: {str(e)}")
        return f"Error: {str(e)}"
