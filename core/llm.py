from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.messages import HumanMessage, AIMessage
# from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


load_dotenv()

# -----------------------------
# ✅ LLM
# -----------------------------
def get_llm():
    try:
        logger.info("initializing LLM...")
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL"),
            model=os.getenv("MODEL_NAME")
        )
    except Exception as e:
        raise RuntimeError(f"LLM init failed: {e}")

# def get_llm():
#     try:
#         logger.info("initializing LLM...")
#         return ChatAnthropic(
#             model=os.getenv("MODEL_NAME"),
#             anthropic_api_key=os.getenv("CLAUDE_API_KEY")
#         )
#     except Exception as e:
#         raise RuntimeError(f"LLM init failed: {e}")


# -----------------------------
# ✅ Dynamic Prompt Template
# -----------------------------
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
    try:
        if history is None:
            history = []

        llm = get_llm()
        prompt_template = get_prompt_template(system)

        chain = prompt_template | llm

        response = chain.invoke({
            "history": build_history(history),
            "input": str(prompt)
        })

        return response.content

    except Exception as e:
        return f"Error: {str(e)}"
