"""Local FastMCP server that exposes the DDGS web search tool."""

from ddgs import DDGS
from mcp.server.fastmcp import FastMCP


mcp = FastMCP("OmniClaw MCP Server")


@mcp.tool()
def ddgs_search(query: str, max_results: int = 3) -> list[dict[str, str]]:
    """Search the web with DDGS and return simple structured results."""
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    formatted_results: list[dict[str, str]] = []

    for item in results:
        # Only the fields the app already uses are returned here.
        formatted_results.append(
            {
                "title": str(item.get("title", "")),
                "href": str(item.get("href", "")),
                "body": str(item.get("body", "")),
            }
        )

    return formatted_results


if __name__ == "__main__":
    mcp.run(transport="stdio")


    
