"""DuckDuckGo MCP search helpers for OmniClaw."""

import json
import logging
from typing import Any

from mcp.mcp_client import call_tool


logger = logging.getLogger(__name__)

DUCKDUCKGO_SEARCH_TOOL = "duckduckgo_search"
MCP_SEARCH_FALLBACK_MESSAGE = "DuckDuckGo MCP search is unavailable right now."


def build_duckduckgo_server_config() -> dict[str, Any]:
    """
    Build the MCP server config for DuckDuckGo search.

    This uses the DuckDuckGo MCP CLI command in stdio mode.
    """
    logger.info("Building DuckDuckGo MCP server config")

    return {
        "command": "duckduckgo-mcp",
        "args": ["serve"],
        "env": None,
    }


def build_duckduckgo_search_arguments(query: str) -> dict[str, Any]:
    """
    Build the input arguments for the DuckDuckGo MCP search tool.

    The output is requested as JSON so it is easier to format cleanly.
    """
    logger.info("Building DuckDuckGo MCP search arguments")

    return {
        "query": query,
        "max_results": 3,
        "safesearch": "moderate",
        "output_format": "json",
    }


def parse_json_result(raw_result: str) -> Any:
    """
    Parse the MCP result string into JSON when possible.

    If parsing fails, the original string is returned unchanged.
    """
    try:
        logger.info("Trying to parse DuckDuckGo MCP result as JSON")
        return json.loads(raw_result)
    except Exception:
        logger.info("DuckDuckGo MCP result was not JSON, using raw text")
        return raw_result


def extract_result_items(parsed_result: Any) -> list[dict[str, Any]]:
    """
    Pull the list of search result items from the DuckDuckGo response.

    A few simple response shapes are checked to keep this readable.
    """
    logger.info("Extracting DuckDuckGo search result items")

    if isinstance(parsed_result, list):
        return [item for item in parsed_result if isinstance(item, dict)]

    if isinstance(parsed_result, dict):
        if isinstance(parsed_result.get("results"), list):
            return [item for item in parsed_result["results"] if isinstance(item, dict)]

        if isinstance(parsed_result.get("data"), list):
            return [item for item in parsed_result["data"] if isinstance(item, dict)]

    return []


def format_result_item(item: dict[str, Any], index: int) -> str:
    """
    Format one DuckDuckGo search result into a readable text block.

    Each result shows the title, URL, and snippet.
    """
    logger.info("Formatting DuckDuckGo MCP result item %s", index)

    title = str(item.get("title") or item.get("name") or f"Result {index}")
    url = str(item.get("href") or item.get("url") or item.get("link") or "No link available.")
    snippet = str(item.get("body") or item.get("snippet") or item.get("description") or "No snippet available.")

    return f"{index}. {title}\nLink: {url}\nSummary: {snippet}"


def format_search_results(parsed_result: Any, raw_result: str) -> str:
    """
    Turn the DuckDuckGo MCP response into a clean readable string.

    If structured results are not found, the raw text is returned.
    """
    logger.info("Formatting DuckDuckGo MCP search results")

    result_items = extract_result_items(parsed_result)
    if not result_items:
        logger.info("No structured DuckDuckGo items found, returning raw text")
        return raw_result.strip() or "No results found."

    formatted_items: list[str] = []

    for index, item in enumerate(result_items, start=1):
        # Each item is formatted separately so the output stays easy to scan.
        formatted_items.append(format_result_item(item, index))

    return "\n\n".join(formatted_items)


def search_via_mcp(query: str) -> str:
    """
    Search the web through the DuckDuckGo MCP server.

    A fallback message is returned if the MCP search call fails.
    """
    try:
        logger.info("Using DuckDuckGo MCP search for query: %s", query)

        server_config = build_duckduckgo_server_config()
        tool_arguments = build_duckduckgo_search_arguments(query)

        # The shared MCP client handles the server connection and tool call.
        raw_result = call_tool(
            command=server_config["command"],
            tool_name=DUCKDUCKGO_SEARCH_TOOL,
            arguments=tool_arguments,
            args=server_config["args"],
            env=server_config["env"],
        )

        parsed_result = parse_json_result(raw_result)
        formatted_result = format_search_results(parsed_result, raw_result)

        logger.info("DuckDuckGo MCP search completed successfully")
        return formatted_result

    except Exception as exc:
        logger.error("DuckDuckGo MCP search failed: %s", str(exc))
        # TODO: Add more free MCP search providers here later.
        return f"{MCP_SEARCH_FALLBACK_MESSAGE} Error: {str(exc)}"
