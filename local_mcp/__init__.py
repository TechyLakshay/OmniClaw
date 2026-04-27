"""Local MCP package.

Public imports are exposed here so other modules can use:
`from local_mcp import run_mcp_tool, list_all_tools`.
"""

from local_mcp.service import call_mcp_tool, list_all_tools, run_mcp_tool

__all__ = ["list_all_tools", "call_mcp_tool", "run_mcp_tool"]
