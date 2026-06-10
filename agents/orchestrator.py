# import logging

<<<<<<< HEAD
from core.llm import invoke_llm
from tools.research_tool import run_research_tool
from tools.writer_tool import run_writer_tool
=======
# from core.llm import invoke_llm
# from local_mcp.service import list_all_tools, run_mcp_tool
# from tools.research_tool import run_research_tool
# from tools.writer_tool import run_writer_tool
>>>>>>> f3df47a (add new tool -> password genrator(MCP))


# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# logger = logging.getLogger(__name__)


<<<<<<< HEAD
ORCHESTRATOR_SYSTEM = """
=======
# # ORCHESTRATOR_SYSTEM = """
# # You are the only agent in the system.

# # Decide the best next action for the user request.

# # Available actions:
# # - RESEARCH_TOOL -> facts, search, current information, summaries based on search
# # - WRITER_TOOL -> create structured markdown and save notes/content
# # - CHAT -> normal direct conversation without tool use

# # Rules:
# # - Answer with ONLY ONE TOKEN
# # - No explanation
# # - Reply with exactly one of: RESEARCH_TOOL, WRITER_TOOL, CHAT
# # """

# ORCHESTRATOR_SYSTEM = """
# You are the only agent in the system.

# Decide the best next action for the user request.

# Available actions:
# - RESEARCH_TOOL -> facts, search, current information, summaries based on search
# - WRITER_TOOL -> create structured markdown and save notes/content
# - CALCULATOR -> add two numbers
# - PASSWORD -> generate a strong password, check password strength
# - CHAT -> normal direct conversation without tool use


# Rules:
# - Answer with ONLY ONE TOKEN
# - No explanation
# - Reply with exactly one of: RESEARCH_TOOL, WRITER_TOOL, CALCULATOR, PASSWORD, CHAT
# """

# def run_chat_agent(message: str, history: list) -> str:
#     logger.info("running chat agent...")
#     return invoke_llm(
#         prompt=message,
#         system="You are NanoClaw, a helpful AI assistant. Be concise, clear, and friendly and answer accurately.",
#         history=history,
#     )


# TOOLS = {
#     "RESEARCH_TOOL": run_research_tool,
#     "WRITER_TOOL": run_writer_tool,
#     "CALCULATOR": run_mcp_tool,
#     "PASSWORD": run_mcp_tool,
#     "CHAT": run_chat_agent,
    
# }


# def decide_agent(message: str, history: list) -> str:
#     try:
#         logger.info("deciding tool usage...")
#         response = invoke_llm(
#             prompt=message,
#             system=ORCHESTRATOR_SYSTEM,
#             history=history,
#         )

#         decision = response.strip().upper()
#         logger.info(f"Raw Decision: {decision}")

#         if "RESEARCH_TOOL" in decision:
#             return "RESEARCH_TOOL"
#         if "WRITER_TOOL" in decision:
#             return "WRITER_TOOL"
#         if "CALCULATOR" in decision:
#             return "CALCULATOR"
#         if "PASSWORD" in decision:
#             return "PASSWORD"
#         if "CHAT" in decision:
#             return "CHAT"
        
#         return "CHAT"

#     except Exception as exc:
#         logger.error(f"Decision error: {str(exc)}")
#         return "CHAT"


# def run_orchestrator(message: str, history: list | None = None) -> str:
#     history = history or []

#     try:
#         decision = decide_agent(message, history)
#         logger.info(f"Routing -> {decision}")

#         tool_fn = TOOLS.get(decision, run_chat_agent)

#         if decision == "WRITER_TOOL":
#             return tool_fn(message, filename="note", history=history)

#         return tool_fn(message, history)

#     except Exception as exc:
#         logger.error(f"Orchestrator error: {str(exc)}")
#         return "Something went wrong."


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
>>>>>>> f3df47a (add new tool -> password genrator(MCP))
You are the only agent in the system.

Decide the best next action for the user request.

Available actions:
<<<<<<< HEAD
- RESEARCH_TOOL -> facts, search, current information, summaries based on search
- WRITER_TOOL -> create structured markdown and save notes/content
- CHAT -> normal direct conversation without tool use
=======
{actions_text}
>>>>>>> f3df47a (add new tool -> password genrator(MCP))

Rules:
- Answer with ONLY ONE TOKEN
- No explanation
<<<<<<< HEAD
- Reply with exactly one of: RESEARCH_TOOL, WRITER_TOOL, CHAT
=======
- Reply with exactly one of: {token_list}
>>>>>>> f3df47a (add new tool -> password genrator(MCP))
"""


def run_chat_agent(message: str, history: list) -> str:
    logger.info("running chat agent...")
    return invoke_llm(
        prompt=message,
        system="You are NanoClaw, a helpful AI assistant. Be concise, clear, and friendly and answer accurately.",
        history=history,
    )


<<<<<<< HEAD
TOOLS = {
    "RESEARCH_TOOL": run_research_tool,
    "WRITER_TOOL": run_writer_tool,
    "CHAT": run_chat_agent,
}


=======
>>>>>>> f3df47a (add new tool -> password genrator(MCP))
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
<<<<<<< HEAD
        if "CHAT" in decision:
            return "CHAT"
=======
        if decision.startswith("MCP:"):
            return decision
>>>>>>> f3df47a (add new tool -> password genrator(MCP))

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