import logging

from core.llm import invoke_llm
from local_mcp.service import list_all_tools, run_mcp_tool
from tools.research_tool import run_research_tool
from tools.writer_tool import run_writer_tool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

_STATIC_ACTIONS = [
    "RESEARCH_TOOL -> facts, search, current information, summaries based on search",
    "WRITER_TOOL   -> create structured markdown and save notes/content",
    "CHAT          -> normal direct conversation without tool use",
]


def build_orchestrator_system() -> str:
    """Build the system prompt dynamically from registered MCP tools."""
    try:
        mcp_tools = list_all_tools()
        mcp_lines = [
            f"MCP:{t['name'].upper()} -> {t['description']}"
            for t in mcp_tools
        ]
        mcp_tokens = ", ".join(f"MCP:{t['name'].upper()}" for t in mcp_tools)
    except Exception as e:
        logger.warning(f"Could not load MCP tools for prompt: {e}")
        mcp_lines = []
        mcp_tokens = ""

    all_actions = _STATIC_ACTIONS + mcp_lines
    actions_text = "\n".join(f"- {a}" for a in all_actions)

    static_tokens = "RESEARCH_TOOL, WRITER_TOOL, CHAT"
    token_list = f"{static_tokens}, {mcp_tokens}" if mcp_tokens else static_tokens

    return f"""
You are the only agent in the system.

Decide the best next action for the user request.

Available actions:
{actions_text}

Rules:
- Answer with ONLY ONE TOKEN
- No explanation
- Reply with exactly one of: {token_list}
"""


def run_chat_agent(message: str, history: list) -> str:
    logger.info("running chat agent...")
    return invoke_llm(
        prompt=message,
        system="You are NanoClaw, a helpful AI assistant. Be concise, clear, and friendly and answer accurately.",
        history=history,
    )


def decide_agent(message: str, history: list) -> str:
    try:
        logger.info("deciding tool usage...")
        system = build_orchestrator_system()
        response = invoke_llm(prompt=message, system=system, history=history)

        decision = response.strip().upper()
        logger.info(f"Raw Decision: {decision}")

        if "RESEARCH_TOOL" in decision:
            return "RESEARCH_TOOL"
        if "WRITER_TOOL" in decision:
            return "WRITER_TOOL"
        if decision.startswith("MCP:"):
            return decision

        return "CHAT"

    except Exception as exc:
        logger.error(f"Decision error: {str(exc)}")
        return "CHAT"


def run_orchestrator(message: str, history: list | None = None) -> str:
    history = history or []

    try:
        decision = decide_agent(message, history)
        logger.info(f"Routing -> {decision}")

        if decision == "RESEARCH_TOOL":
            return run_research_tool(message, history)

        if decision == "WRITER_TOOL":
            return run_writer_tool(message, filename="note", history=history)

        if decision.startswith("MCP:"):
            return run_mcp_tool(message, history)

        return run_chat_agent(message, history)

    except Exception as exc:
        logger.error(f"Orchestrator error: {str(exc)}")
        return "Something went wrong."