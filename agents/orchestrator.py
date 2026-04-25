import logging

from core.llm import invoke_llm
from tools.research_tool import run_research_tool
from tools.writer_tool import run_writer_tool


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


ORCHESTRATOR_SYSTEM = """
You are the only agent in the system.

Decide the best next action for the user request.

Available actions:
- RESEARCH_TOOL -> facts, search, current information, summaries based on search
- WRITER_TOOL -> create structured markdown and save notes/content
- CHAT -> normal direct conversation without tool use

Rules:
- Answer with ONLY ONE TOKEN
- No explanation
- Reply with exactly one of: RESEARCH_TOOL, WRITER_TOOL, CHAT
"""


def run_chat_agent(message: str, history: list) -> str:
    """Run the normal chat path when no tool is needed."""
    logger.info("running chat agent...")
    return invoke_llm(
        prompt=message,
        system="You are NanoClaw, a helpful AI assistant. Be concise, clear, and friendly and answer accurately.",
        history=history,
    )


TOOLS = {
    "RESEARCH_TOOL": run_research_tool,
    "WRITER_TOOL": run_writer_tool,
    "CHAT": run_chat_agent,
}


def decide_agent(message: str, history: list) -> str:
    """
    Decide which built-in tool should handle the user message.
    """
    try:
        logger.info("deciding tool usage...")

        response = invoke_llm(
            prompt=message,
            system=ORCHESTRATOR_SYSTEM,
            history=history,
        )

        raw_decision = response.strip()
        decision = raw_decision.upper()
        logger.info(f"Raw Decision: {raw_decision}")

        if "RESEARCH_TOOL" in decision:
            logger.info("LLM selected RESEARCH_TOOL")
            return "RESEARCH_TOOL"
        if "WRITER_TOOL" in decision:
            logger.info("LLM selected WRITER_TOOL")
            return "WRITER_TOOL"
        if "CHAT" in decision:
            logger.info("LLM selected CHAT")
            return "CHAT"

        logger.info("No valid tool selected, defaulting to CHAT")
        return "CHAT"

    except Exception as exc:
        logger.error(f"Decision error: {str(exc)}")
        return "CHAT"


def run_orchestrator(message: str, history: list | None = None) -> str:
    """
    Run the orchestrator and execute a built-in tool.
    """
    history = history or []

    try:
        decision = decide_agent(message, history)
        logger.info(f"Routing -> {decision}")

        if decision in TOOLS:
            logger.info("Routing to tool: %s", decision)
            tool_fn = TOOLS.get(decision, run_chat_agent)

            if decision == "WRITER_TOOL":
                logger.info("Executing WRITER_TOOL")
                return tool_fn(message, filename="note", history=history)

            logger.info("Executing tool")
            return tool_fn(message, history)

        logger.info("Decision is not a valid tool, using CHAT")
        return run_chat_agent(message, history)

    except Exception as exc:
        logger.error(f"Orchestrator error: {str(exc)}")
        return "Something went wrong."
