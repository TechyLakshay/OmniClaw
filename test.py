"""Simple local script for testing MCP connections."""

import logging

from core.mcp_client import get_default_filesystem_config
from core.mcp_client import list_tools
from tools.duckduckgo_mcp import build_duckduckgo_search_arguments
from tools.duckduckgo_mcp import build_duckduckgo_server_config
from tools.duckduckgo_mcp import format_search_results
from tools.duckduckgo_mcp import parse_json_result


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def test_filesystem_tools() -> None:
    """Test listing tools from the default filesystem MCP server."""
    try:
        logger.info("Testing filesystem MCP tool listing")

        # The filesystem server is the easiest local MCP server to test first.
        server_config = get_default_filesystem_config()
        tools = list_tools(
            command=server_config["command"],
            args=server_config["args"],
            env=server_config["env"],
        )

        print("Filesystem MCP tools:")
        print(tools)

    except Exception as exc:
        logger.error("Filesystem MCP test failed: %s", str(exc))
        print(f"Filesystem MCP test failed: {str(exc)}")


def test_duckduckgo_search() -> None:
    """Test calling DuckDuckGo Search through the MCP search helper."""
    try:
        logger.info("Testing DuckDuckGo Search MCP tool call")

        # This uses the DuckDuckGo MCP server configuration from the search helper.
        server_config = build_duckduckgo_server_config()
        search_arguments = build_duckduckgo_search_arguments("Python FastAPI tutorial")

        from core.mcp_client import call_tool

        raw_result = call_tool(
            command=server_config["command"],
            tool_name="duckduckgo_search",
            arguments=search_arguments,
            args=server_config["args"],
            env=server_config["env"],
        )

        parsed_result = parse_json_result(raw_result)
        formatted_result = format_search_results(parsed_result, raw_result)

        print("\nDuckDuckGo Search MCP result:")
        print(formatted_result)

    except Exception as exc:
        logger.error("DuckDuckGo Search MCP test failed: %s", str(exc))
        print(f"DuckDuckGo Search MCP test failed: {str(exc)}")


def main() -> None:
    """Run the available MCP connection tests step by step."""
    test_filesystem_tools()
    test_duckduckgo_search()


if __name__ == "__main__":
    main()
