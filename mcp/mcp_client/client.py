"""Simple MCP client helpers for OmniClaw."""

import asyncio
import json
import os
import threading
from typing import Any

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError as exc:  # pragma: no cover - depends on optional package installation
    ClientSession = None  # type: ignore[assignment]
    StdioServerParameters = None  # type: ignore[assignment]
    stdio_client = None  # type: ignore[assignment]
    MCP_IMPORT_ERROR = exc
else:
    MCP_IMPORT_ERROR = None


def build_filesystem_server_config(root_path: str) -> dict[str, Any]:
    """
    Build a simple MCP server config for the filesystem server example.

    This uses the official filesystem MCP server through `npx`.
    """
    return {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", root_path],
        "env": None,
    }


def get_default_filesystem_config() -> dict[str, Any]:
    """
    Build the default filesystem MCP config for the current working directory.

    This gives the client an easy example server to connect to first.
    """
    root_path = os.getcwd()
    return build_filesystem_server_config(root_path)


def ensure_mcp_installed() -> None:
    """
    Check that the MCP Python package is installed before using the client.

    A clear error is raised if the package is missing.
    """
    if MCP_IMPORT_ERROR is not None:
        message = "The `mcp` package is not installed. Run `pip install mcp` before using the MCP client."
        raise RuntimeError(message) from MCP_IMPORT_ERROR


def build_server_parameters(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> StdioServerParameters:
    """
    Create MCP stdio server parameters from simple command values.

    This keeps transport setup in one small place.
    """
    ensure_mcp_installed()

    return StdioServerParameters(
        command=command,
        args=args or [],
        env=env,
    )


def extract_text_from_content_item(content_item: Any) -> str:
    """
    Convert one MCP content item into plain text.

    Different MCP servers may return text or structured content blocks.
    """
    text_value = getattr(content_item, "text", None)
    if text_value is not None:
        return str(text_value)

    try:
        # `model_dump()` is the safest way to stringify Pydantic MCP objects.
        dumped_value = content_item.model_dump()
        return json.dumps(dumped_value, ensure_ascii=False)
    except Exception:
        return str(content_item)


def format_tool_result(result: Any) -> str:
    """
    Turn an MCP tool result into one plain string.

    This keeps the rest of the app from dealing with MCP response objects.
    """
    content = getattr(result, "content", None)
    if content:
        parts = [extract_text_from_content_item(item) for item in content]
        text_parts = [part for part in parts if part.strip()]
        if text_parts:
            return "\n".join(text_parts)

    structured_content = getattr(result, "structuredContent", None)
    if structured_content is not None:
        return json.dumps(structured_content, ensure_ascii=False)

    return str(result)


def run_async_safely(coroutine: Any) -> Any:
    """
    Run an async task from sync code, even if an event loop is already running.

    FastAPI already runs an event loop, so this uses a worker thread in that case.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    result_holder: dict[str, Any] = {}

    def runner() -> None:
        """Run the coroutine in a separate thread with its own event loop."""
        try:
            result_holder["result"] = asyncio.run(coroutine)
        except Exception as exc:
            result_holder["error"] = exc

    thread = threading.Thread(target=runner, daemon=True)
    thread.start()
    thread.join()

    if "error" in result_holder:
        raise result_holder["error"]

    return result_holder.get("result")


async def list_tools_async(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Connect to an MCP server and return the available tool names.

    This is the async version for callers that already use asyncio.
    """
    server_parameters = build_server_parameters(command=command, args=args, env=env)

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # The session must be initialized before any MCP request is sent.
            await session.initialize()
            response = await session.list_tools()
            return [tool.name for tool in response.tools]


async def call_tool_async(
    command: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str:
    """
    Connect to an MCP server, call one tool, and return plain text.

    This is the async version for callers that already use asyncio.
    """
    server_parameters = build_server_parameters(command=command, args=args, env=env)

    async with stdio_client(server_parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # The session must be initialized before any MCP request is sent.
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments or {})
            return format_tool_result(result)


def list_tools(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Connect to an MCP server and return the available tool names.

    This sync wrapper keeps the rest of the project easy to read.
    """
    return run_async_safely(list_tools_async(command=command, args=args, env=env))


def call_tool(
    command: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> str:
    """
    Connect to an MCP server, call one tool, and return plain text.

    This sync wrapper is useful for simple orchestrator code.
    """
    return run_async_safely(
        call_tool_async(
            command=command,
            tool_name=tool_name,
            arguments=arguments,
            args=args,
            env=env,
        )
    )


class MCPClient:
    """
    Simple MCP client wrapper for one server configuration.

    This class stores one server command so the caller does not repeat it.
    """

    def __init__(
        self,
        command: str,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        """
        Store one MCP server configuration for later calls.

        The same client instance can list tools and call tools on that server.
        """
        self.command = command
        self.args = args or []
        self.env = env

    def list_tools(self) -> list[str]:
        """
        List available tools from this client's MCP server.

        The result is a simple list of tool names.
        """
        return list_tools(command=self.command, args=self.args, env=self.env)

    def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> str:
        """
        Call one tool on this client's MCP server.

        The result is always returned as one plain string.
        """
        return call_tool(
            command=self.command,
            tool_name=tool_name,
            arguments=arguments,
            args=self.args,
            env=self.env,
        )


def create_filesystem_mcp_client(root_path: str | None = None) -> MCPClient:
    """
    Create an MCP client for the filesystem server example.

    If no path is given, the current working directory is used.
    """
    config = get_default_filesystem_config() if root_path is None else build_filesystem_server_config(root_path)

    # TODO: Support HTTP MCP servers later if you want remote tool connections.
    return MCPClient(
        command=config["command"],
        args=config["args"],
        env=config["env"],
    )