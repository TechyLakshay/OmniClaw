"""Central MCP server registry.

This module is the single source of truth for:
- Which MCP servers are available
- Which tools each server owns
- How each server process should be launched
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# local_mcp/registry.py -> repo root -> local_mcp/mcp_servers
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SERVERS_DIR = _REPO_ROOT / "local_mcp" / "mcp_servers"


MCP_SERVERS: dict[str, dict[str, Any]] = {
    "calculator": {
        # Use the same python interpreter as the running app.
        "command": sys.executable,
        "args": [str(_SERVERS_DIR / "calculator_server.py")],
        "description": "Math tools: add_numbers, get_current_time",
        "tools": ["add_numbers", "get_current_time"],
    },
    "password": {
        "command": sys.executable,
        "args": [str(_SERVERS_DIR / "password_server.py")],
        "description": "Password tools: generate_password, check_password_strength",
        "tools": ["generate_password", "check_password_strength"],
    },
}


def get_server_for_tool(tool_name: str) -> dict[str, Any] | None:
    """Return the server configuration that owns ``tool_name``."""
    for server in MCP_SERVERS.values():
        if tool_name in server.get("tools", []):
            return server
    return None

