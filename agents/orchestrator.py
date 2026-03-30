from core.llm import invoke_llm, build_history
from agents.research_agent import run_research_agent
from agents.writer_agent import run_writer_agent
import logging


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)



logger = logging.getLogger(__name__)


# -----------------------------
# ✅ System Prompt
# -----------------------------
ORCHESTRATOR_SYSTEM = """
You are an Orchestrator Agent.

Classify the user request into ONE category:

RESEARCH → facts, search, information
WRITE → create/save notes or content
CHAT → casual conversation

Rules:
- Answer with ONLY ONE WORD
- No explanation
- Just: RESEARCH or WRITE or CHAT
"""

# -----------------------------
# ✅ Agent Functions
# -----------------------------
def run_chat_agent(message: str, history: list):
    logger.info("running chat agent")
    return invoke_llm(
        prompt=message,
        system="You are NanoClaw, a helpful AI assistant. Be concise.",
        history=history
    )

AGENTS = {
    "RESEARCH": run_research_agent,
    "WRITE": run_writer_agent,
    "CHAT": run_chat_agent
}

# -----------------------------
# ✅ Decide Agent
# -----------------------------
def decide_agent(message: str, history: list) -> str:
    try:
        logger.info("deciding agent...")
        response = invoke_llm(
            prompt=message,
            system=ORCHESTRATOR_SYSTEM,
            history=history
        )

        decision = response.strip().upper()
        logger.info(f"Raw Decision: {decision}")

        # ✅ Strong filtering
        if "RESEARCH" in decision:
            return "RESEARCH"
        elif "WRITE" in decision:
            return "WRITE"
        elif "CHAT" in decision:
            return "CHAT"

        return "CHAT"

    except Exception as e:
        logger.error(f"Decision error: {str(e)}")
        return "CHAT"

# -----------------------------
# ✅ Main Orchestrator
# -----------------------------
def run_orchestrator(message: str, history: list = None):
    if history is None:
        history = []

    try:
        decision = decide_agent(message, history)
        logger.info(f"Routing → {decision}")

        agent_fn = AGENTS.get(decision, run_chat_agent)

        if decision == "WRITE":
            return agent_fn(message, filename="note", history=history)

        return agent_fn(message, history)

    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        return "Something went wrong."