"""Router for choosing MCP search first and legacy search second."""

import logging

from tools.duckduckgo_mcp import MCP_SEARCH_FALLBACK_MESSAGE
from tools.duckduckgo_mcp import search_via_mcp
from tools.web_search import web_search


logger = logging.getLogger(__name__)


def mcp_search_failed(search_result: str) -> bool:
    """
    Check if the MCP search result is a fallback message.

    This lets the router decide when to use the legacy search.
    """
    logger.info("Checking whether MCP search returned a fallback message")
    return search_result.startswith(MCP_SEARCH_FALLBACK_MESSAGE)


def run_search(query: str) -> str:
    """
    Run web search with MCP first and the legacy search as backup.

    This keeps search working even when the MCP server is unavailable.
    """
    try:
        logger.info("Trying DuckDuckGo MCP search first")
        mcp_result = search_via_mcp(query)

        if not mcp_search_failed(mcp_result):
            logger.info("Using DuckDuckGo MCP search result")
            return mcp_result

        logger.info("DuckDuckGo MCP failed, using legacy fallback search")
        return web_search(query)

    except Exception as exc:
        logger.error("Search router failed during DuckDuckGo MCP search: %s", str(exc))

        try:
            logger.info("Trying legacy search after router error")
            return web_search(query)
        except Exception as fallback_exc:
            logger.error("Legacy search also failed: %s", str(fallback_exc))
            return f"Search failed: {str(fallback_exc)}"
