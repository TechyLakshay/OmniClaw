"""MCP-based web search helpers for OmniClaw."""

import json
import sys
from pathlib import Path
from typing import Any

from mcp.mcp_client.mcp_client import call_tool


DDGS_SEARCH_TOOL = "ddgs_search"


def build_mcp_server_config() -> dict[str, Any]:
    """
    Build the MCP server config for the local FastMCP DDGS server.

    The same Python interpreter is used so local package imports keep working.
    """
    root_dir = Path(__file__).resolve().parent.parent
    server_file = root_dir / "tools" / "mcp_server.py"

    return {
        "command": sys.executable,
        "args": [str(server_file)],
        "env": None,
    }


def search_via_mcp(query: str) -> str:
    """
    Search the web through the local FastMCP DDGS server.
    """
    server_config = build_mcp_server_config()
    raw_result = call_tool(
        command=server_config["command"],
        tool_name=DDGS_SEARCH_TOOL,
        arguments={
            # The local MCP server only needs the query and a small result count.
            "query": query,
            "max_results": 3,
        },
        args=server_config["args"],
        env=server_config["env"],
    )

    try:
        parsed_result = json.loads(raw_result)
    except Exception:
        # If the server returned plain text, we pass that through as-is.
        return raw_result.strip() or "No results found."

    if isinstance(parsed_result, dict) and isinstance(parsed_result.get("results"), list):
        result_items = [item for item in parsed_result["results"] if isinstance(item, dict)]
    elif isinstance(parsed_result, list):
        result_items = [item for item in parsed_result if isinstance(item, dict)]
    else:
        result_items = []

    if not result_items:
        return raw_result.strip() or "No results found."

    formatted_items: list[str] = []

    for index, item in enumerate(result_items, start=1):
        # Each item is formatted here because the logic is only used in this one place.
        title = str(item.get("title") or item.get("name") or f"Result {index}")
        link = str(item.get("href") or item.get("url") or "No link available.")
        snippet = str(item.get("body") or item.get("snippet") or item.get("description") or "No snippet available.")
        formatted_items.append(f"{index}. {title}\nLink: {link}\nSummary: {snippet}")

    return "\n\n".join(formatted_items)
