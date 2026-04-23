"""MCP-based web search helpers for OmniClaw."""

import json
import logging
import os
from typing import Any

from core.mcp_client import call_tool


logger = logging.getLogger(__name__)

BRAVE_WEB_SEARCH_TOOL = "brave_web_search"
MCP_SEARCH_FALLBACK_MESSAGE = "MCP search is unavailable right now."


def build_brave_server_config() -> dict[str, Any]:
    """
    Build the MCP server config for Brave Search.

    This reads the Brave API key from the environment.
    """
    logger.info("Building Brave Search MCP server config")

    brave_api_key = os.getenv("BRAVE_API_KEY")
    if not brave_api_key:
        message = "BRAVE_API_KEY is missing for Brave Search MCP."
        logger.error(message)
        raise RuntimeError(message)

    return {
        "command": "npx",
        "args": ["-y", "@brave/brave-search-mcp-server", "--transport", "stdio"],
        "env": {
            "BRAVE_API_KEY": brave_api_key,
        },
    }


def build_brave_search_arguments(query: str) -> dict[str, Any]:
    """
    Build the input arguments for the Brave web search tool.

    The values are kept small and simple for the first version.
    """
    logger.info("Building Brave Search MCP arguments")

    return {
        "query": query,
        "count": 3,
        "search_lang": "en",
        "country": "US",
        "safesearch": "moderate",
    }


def parse_json_result(raw_result: str) -> Any:
    """
    Parse the MCP result string into JSON when possible.

    If the result is not JSON, the original string is returned.
    """
    try:
        logger.info("Trying to parse MCP search result as JSON")
        return json.loads(raw_result)
    except Exception:
        logger.info("MCP search result was not JSON, using raw text")
        return raw_result


def extract_result_items(parsed_result: Any) -> list[dict[str, Any]]:
    """
    Pull the list of search result items from the Brave response.

    Different response shapes are checked one by one to keep this robust.
    """
    logger.info("Extracting result items from Brave MCP response")

    if isinstance(parsed_result, dict):
        if isinstance(parsed_result.get("results"), list):
            return parsed_result["results"]

        web_section = parsed_result.get("web")
        if isinstance(web_section, dict) and isinstance(web_section.get("results"), list):
            return web_section["results"]

        data_section = parsed_result.get("data")
        if isinstance(data_section, dict) and isinstance(data_section.get("results"), list):
            return data_section["results"]

    return []


def format_result_item(item: dict[str, Any], index: int) -> str:
    """
    Format one search result item into a readable text block.

    Each block includes the title and snippet for easy reading.
    """
    logger.info("Formatting Brave MCP result item %s", index)

    title = str(item.get("title") or item.get("name") or f"Result {index}")
    snippet = str(item.get("description") or item.get("snippet") or item.get("body") or "No snippet available.")

    return f"{index}. {title}\n{snippet}"


def format_search_results(parsed_result: Any, raw_result: str) -> str:
    """
    Turn the Brave MCP response into a clean readable string.

    If structured items are not found, the raw MCP text is returned.
    """
    logger.info("Formatting Brave MCP search results")

    result_items = extract_result_items(parsed_result)
    if not result_items:
        logger.info("No structured search items found, returning raw MCP text")
        return raw_result.strip() or "No results found."

    formatted_items: list[str] = []

    for index, item in enumerate(result_items, start=1):
        # Each result is formatted one by one so the output stays easy to read.
        formatted_items.append(format_result_item(item, index))

    return "\n\n".join(formatted_items)


def search_via_mcp(query: str) -> str:
    """
    Search the web through the Brave Search MCP server.

    A fallback message is returned if MCP search fails.
    """
    try:
        logger.info("Using MCP search for query: %s", query)

        server_config = build_brave_server_config()
        tool_arguments = build_brave_search_arguments(query)

        # The generic MCP client handles the actual server connection and tool call.
        raw_result = call_tool(
            command=server_config["command"],
            tool_name=BRAVE_WEB_SEARCH_TOOL,
            arguments=tool_arguments,
            args=server_config["args"],
            env=server_config["env"],
        )

        parsed_result = parse_json_result(raw_result)
        formatted_result = format_search_results(parsed_result, raw_result)

        logger.info("MCP search completed successfully")
        return formatted_result

    except Exception as exc:
        logger.error("MCP search failed: %s", str(exc))
        # TODO: Add more MCP search providers here later.
        return f"{MCP_SEARCH_FALLBACK_MESSAGE} Error: {str(exc)}"
