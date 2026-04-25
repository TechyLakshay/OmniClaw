"""Router for web search."""

import logging

from tools.web_search import web_search


logger = logging.getLogger(__name__)


def run_search(query: str) -> str:
    """
    Run web search using DDGS.
    """
    try:
        return web_search(query)
    except Exception as exc:
        logger.error("Search failed: %s", str(exc))
        return f"Search failed: {str(exc)}"
