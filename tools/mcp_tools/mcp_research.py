"""
MCP Research Tool - DuckDuckGo search via MCP with @mcp.tool wrapper.

This wraps the DuckDuckGo MCP search as a tool for orchestrator use.
"""

import logging
from mcp.mcp_servers.duckduckgo_server import search_via_mcp


logger = logging.getLogger(__name__)


def run_mcp_research(query: str, history: list | None = None) -> str:
    """
    Run research using MCP DuckDuckGo search.
    
    This is the main entry point for orchestrator to call.
    
    Args:
        query: Search query
        history: Message history (unused but kept for compatibility)
        
    Returns:
        Search results formatted as string
    """
    try:
        logger.info(f"MCP Research: {query}")
        results = search_via_mcp(query)
        logger.info("MCP Research completed")
        return results
    except Exception as exc:
        logger.error(f"MCP Research failed: {exc}")
        return f"Research failed: {str(exc)}"
