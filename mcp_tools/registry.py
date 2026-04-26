# mcp_tools/registry.py
import os

_SERVERS_DIR = os.path.join(os.path.dirname(__file__), "../local_mcp/mcp_servers")

# Maps a server name -> command to launch it via stdio
MCP_SERVERS = {
    "calculator": {
        "command": "python",
        "args": [os.path.join(_SERVERS_DIR, "calculator_server.py")],
        "description": "Math tools: add_numbers, get_current_time",
        "tools": ["add_numbers", "get_current_time"],
    },
    # Add new servers here as you build them — one entry per server file
}

def get_server_for_tool(tool_name: str) -> dict | None:
    """Look up which server owns a given tool name."""
    for server in MCP_SERVERS.values():
        if tool_name in server["tools"]:
            return server
    return None