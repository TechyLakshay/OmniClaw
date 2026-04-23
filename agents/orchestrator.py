import asyncio
import logging

from core.llm import invoke_llm
from core.mcp_client import call_tool as call_mcp_tool
from core.mcp_client import get_default_filesystem_config
from core.mcp_client import list_tools_async
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


async def get_mcp_tools() -> list[str]:
    """
    Get the list of available MCP tool names.

    This returns an empty list if MCP is not available so the app never crashes.
    """
    try:
        logger.info("Checking for available MCP tools")

        # Start with the default filesystem MCP server example from the MCP client.
        # TODO: Add support for more MCP servers here later.
        server_config = get_default_filesystem_config()

        tool_names = await list_tools_async(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config["env"],
        )

        logger.info("MCP tools found: %s", tool_names)
        return tool_names

    except Exception as exc:
        logger.error("MCP tools are unavailable: %s", str(exc))
        return []


def get_mcp_tools_sync() -> list[str]:
    """
    Get MCP tool names from synchronous code.

    This wrapper keeps the rest of the orchestrator simple and readable.
    """
    try:
        logger.info("Loading MCP tools through sync wrapper")
        return asyncio.run(get_mcp_tools())
    except Exception as exc:
        logger.error("Failed to load MCP tools in sync wrapper: %s", str(exc))
        return []


def build_orchestrator_system(mcp_tools: list[str]) -> str:
    """
    Build the system prompt for the orchestrator.

    MCP tool names are added only when they are available.
    """
    logger.info("Building orchestrator system prompt")

    if not mcp_tools:
        logger.info("No MCP tools available, using base orchestrator prompt")
        return ORCHESTRATOR_SYSTEM

    mcp_lines = "\n".join([f"- {tool_name}" for tool_name in mcp_tools])

    return f"""
You are the only agent in the system.

Decide the best next action for the user request.

Available actions:
- RESEARCH_TOOL -> facts, search, current information, summaries based on search
- WRITER_TOOL -> create structured markdown and save notes/content
- CHAT -> normal direct conversation without tool use

Available MCP tools:
{mcp_lines}

Rules:
- Answer with ONLY ONE TOKEN
- No explanation
- Reply with exactly one tool name
- You may reply with RESEARCH_TOOL, WRITER_TOOL, CHAT, or one MCP tool name from the list above
"""


def match_mcp_tool_name(decision: str, mcp_tools: list[str]) -> str | None:
    """
    Match an LLM decision to a real MCP tool name.

    This handles exact matches and simple uppercase matches safely.
    """
    logger.info("Matching decision against MCP tools: %s", decision)

    for tool_name in mcp_tools:
        # Exact matching is tried first so original MCP tool names are preserved.
        if decision == tool_name:
            logger.info("Matched MCP tool by exact name: %s", tool_name)
            return tool_name

    for tool_name in mcp_tools:
        # Uppercase matching helps when the LLM normalizes the tool name.
        if decision.upper() == tool_name.upper():
            logger.info("Matched MCP tool by uppercase name: %s", tool_name)
            return tool_name

    logger.info("No MCP tool matched the decision")
    return None


def execute_mcp_tool(tool_name: str, message: str, history: list) -> str:
    """
    Call one MCP tool and return its result as plain text.

    If MCP fails, this returns the normal chat response instead of crashing.
    """
    try:
        logger.info("Preparing to execute MCP tool: %s", tool_name)

        # Start with the default filesystem MCP server example from the MCP client.
        # TODO: Route different MCP tools to different MCP servers later.
        server_config = get_default_filesystem_config()

        # These generic arguments give MCP tools some useful context.
        tool_arguments = {
            "message": message,
            "input": message,
            "query": message,
            "history": history,
        }

        logger.info("Calling MCP tool with generic message context: %s", tool_name)
        return call_mcp_tool(
            command=server_config["command"],
            tool_name=tool_name,
            arguments=tool_arguments,
            args=server_config["args"],
            env=server_config["env"],
        )

    except Exception as exc:
        logger.error("MCP tool execution failed for %s: %s", tool_name, str(exc))
        logger.info("Falling back to chat after MCP failure")
        return run_chat_agent(message, history)


def decide_agent(message: str, history: list) -> str:
    """
    Decide which tool or chat path should handle the user message.

    MCP tools are included in the prompt when they are available.
    """
    try:
        logger.info("deciding tool usage...")
        
        # Step 1: Ask MCP for any available tool names.
        mcp_tools = get_mcp_tools_sync()
        logger.info("Available MCP tools for decision: %s", mcp_tools)

        # Step 2: Build the prompt that includes the normal tools plus MCP tools.
        system_prompt = build_orchestrator_system(mcp_tools)

        response = invoke_llm(
            prompt=message,
            system=system_prompt,
            history=history,
        )

        raw_decision = response.strip()
        decision = raw_decision.upper()
        logger.info(f"Raw Decision: {raw_decision}")

        if "RESEARCH_TOOL" in decision:
            logger.info("LLM selected built-in RESEARCH_TOOL")
            return "RESEARCH_TOOL"
        if "WRITER_TOOL" in decision:
            logger.info("LLM selected built-in WRITER_TOOL")
            return "WRITER_TOOL"
        if "CHAT" in decision:
            logger.info("LLM selected built-in CHAT")
            return "CHAT"

        # Step 3: If the decision is not one of the built-in tools, try MCP.
        matched_mcp_tool = match_mcp_tool_name(raw_decision, mcp_tools)
        if matched_mcp_tool is not None:
            logger.info("LLM selected MCP tool: %s", matched_mcp_tool)
            return matched_mcp_tool

        logger.info("No valid tool selected, defaulting to CHAT")
        return "CHAT"

    except Exception as exc:
        logger.error(f"Decision error: {str(exc)}")
        return "CHAT"


def run_orchestrator(message: str, history: list | None = None) -> str:
    """
    Run the orchestrator and execute either a built-in tool or an MCP tool.

    Existing built-in tool behavior is preserved exactly, with MCP as a bonus layer.
    """
    history = history or []

    try:
        decision = decide_agent(message, history)
        logger.info(f"Routing -> {decision}")

        # Step 1: Keep the original built-in tool routing exactly as before.
        if decision in TOOLS:
            logger.info("Routing to built-in tool: %s", decision)
            tool_fn = TOOLS.get(decision, run_chat_agent)

            if decision == "WRITER_TOOL":
                logger.info("Executing WRITER_TOOL with existing filename flow")
                return tool_fn(message, filename="note", history=history)

            logger.info("Executing built-in tool with existing flow")
            return tool_fn(message, history)

        # Step 2: If the decision is not built-in, treat it as an MCP tool name.
        logger.info("Decision is not a built-in tool, trying MCP tool execution")
        return execute_mcp_tool(decision, message, history)

    except Exception as exc:
        logger.error(f"Orchestrator error: {str(exc)}")
        return "Something went wrong."
