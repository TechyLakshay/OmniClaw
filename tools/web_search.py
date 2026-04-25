# LEGACY: kept as fallback if MCP search is unavailable
import logging

from ddgs import DDGS


logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web with DDGS and return a readable plain text result."""
    try:
        logger.info("Running legacy DDGS web search for query: %s", query)

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

            if not results:
                logger.info("DDGS search returned no results")
                return "No results found."

            output = ""

            for r in results:
                output += f"Title: {r['title']}\n"
                output += f"Link: {r['href']}\n"
                output += f"Summary: {r['body']}\n\n"

            logger.info("DDGS search completed successfully")
            return output.strip()
    except Exception as exc:
        logger.error("DDGS search failed: %s", str(exc))
        return f"Search failed: {str(exc)}"


def run_ddgs_search(query: str) -> str:
    """Run a simple DDGS search wrapper for quick local testing."""
    try:
        logger.info("Running DDGS search wrapper")

        # This wrapper keeps test code simple and uses the existing legacy search.
        return web_search(query=query, max_results=3)
    except Exception as exc:
        logger.error("DDGS search wrapper failed: %s", str(exc))
        return f"Search failed: {str(exc)}"
