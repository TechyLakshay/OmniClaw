from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import HumanMessage, AIMessage
# from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os
import logging
import time
from pathlib import Path



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
def get_llm(
    model: str = "qwen2.5:7b",
    temperature: float = 0.7,
):
    start_time = time.perf_counter()
    logger.info(f"llm:get_llm:start model={model} temperature={temperature}")

    if "/" in model:
        raise ValueError(f"Invalid local model name: {model}")

    llm = ChatOllama(
        base_url="http://localhost:11434",
        model=model,
        temperature=temperature,
    )
    logger.info(f"llm:get_llm:ready elapsed={time.perf_counter() - start_time:.2f}s model={model}")
    return llm
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
def invoke_llm(prompt: str, system: str, history: list = None) -> str:
    """
    Invoke the LLM with proper history and system context.
    
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
        llm = get_llm()
        logger.info(f"llm:invoke:client_ready elapsed={time.perf_counter() - llm_start:.2f}s")

        context_start = time.perf_counter()
        core_context = load_core_context()
        final_system = system if not core_context else f"{core_context}\n\n[Task Prompt]\n{system}"
        prompt_template = get_prompt_template(final_system)
        logger.info(
            f"llm:invoke:prompt_ready elapsed={time.perf_counter() - context_start:.2f}s "
            f"final_system_len={len(final_system)}"
        )

        chain = prompt_template | llm

        invoke_start = time.perf_counter()
        logger.info("llm:invoke:model_call:start")
        response = chain.invoke({
            "history": build_history(history),
            "input": str(prompt)
        })
        logger.info(
            f"llm:invoke:model_call:done elapsed={time.perf_counter() - invoke_start:.2f}s"
        )

        total_elapsed = time.perf_counter() - total_start
        logger.info(
            f"llm:invoke:success total_elapsed={total_elapsed:.2f}s response_len={len(str(response.content))}"
        )

        return response.content

    except Exception as e:
        logger.error(f"LLM invocation error: {str(e)}")
        return f"Error: {str(e)}"
