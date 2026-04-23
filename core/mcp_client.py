"""Simple MCP client helpers for OmniClaw."""

import asyncio
import json
import logging
import os
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


logger = logging.getLogger(__name__)


def build_filesystem_server_config(root_path: str) -> dict[str, Any]:
    """
    Build a simple MCP server config for the filesystem server example.

    This uses the official filesystem MCP server through `npx`.
    """
    logger.info("Building filesystem MCP server config for path: %s", root_path)

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
    logger.info("Using current working directory for default filesystem MCP server: %s", root_path)
    return build_filesystem_server_config(root_path)


def ensure_mcp_installed() -> None:
    """
    Check that the MCP Python package is installed before using the client.

    A clear error is raised if the package is missing.
    """
    if MCP_IMPORT_ERROR is not None:
        message = "The `mcp` package is not installed. Run `pip install mcp` before using the MCP client."
        logger.error(message)
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

    safe_args = args or []

    logger.info("Creating MCP server parameters for command: %s", command)
    return StdioServerParameters(
        command=command,
        args=safe_args,
        env=env,
    )


async def initialize_session(session: ClientSession) -> None:
    """
    Initialize a connected MCP session.

    The session must be initialized before listing tools or calling tools.
    """
    try:
        logger.info("Initializing MCP session")
        await session.initialize()
    except Exception as exc:
        logger.error("Failed to initialize MCP session: %s", str(exc))
        raise RuntimeError(f"Failed to initialize MCP session: {str(exc)}") from exc


async def fetch_tool_list(session: ClientSession) -> list[str]:
    """
    Get the list of tool names from the connected MCP server.

    Only tool names are returned to keep the output simple.
    """
    try:
        logger.info("Requesting tool list from MCP server")
        response = await session.list_tools()
        return [tool.name for tool in response.tools]
    except Exception as exc:
        logger.error("Failed to list MCP tools: %s", str(exc))
        raise RuntimeError(f"Failed to list MCP tools: {str(exc)}") from exc


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


async def call_tool_on_session(
    session: ClientSession,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
) -> str:
    """
    Call one MCP tool on an active session and return plain text.

    Tool arguments are optional because some tools do not need input.
    """
    try:
        safe_arguments = arguments or {}

        logger.info("Calling MCP tool: %s", tool_name)
        result = await session.call_tool(tool_name, arguments=safe_arguments)
        return format_tool_result(result)
    except Exception as exc:
        logger.error("Failed to call MCP tool `%s`: %s", tool_name, str(exc))
        raise RuntimeError(f"Failed to call MCP tool `{tool_name}`: {str(exc)}") from exc


async def list_tools_async(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Connect to an MCP server and return the available tool names.

    This is the async version for callers that already use asyncio.
    """
    try:
        server_parameters = build_server_parameters(command=command, args=args, env=env)

        logger.info("Opening MCP stdio connection for tool listing")
        async with stdio_client(server_parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await initialize_session(session)
                return await fetch_tool_list(session)
    except Exception as exc:
        logger.error("MCP tool listing failed: %s", str(exc))
        raise RuntimeError(f"MCP tool listing failed: {str(exc)}") from exc


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
    try:
        server_parameters = build_server_parameters(command=command, args=args, env=env)

        logger.info("Opening MCP stdio connection for tool call: %s", tool_name)
        async with stdio_client(server_parameters) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await initialize_session(session)
                return await call_tool_on_session(session, tool_name, arguments)
    except Exception as exc:
        logger.error("MCP tool call failed for `%s`: %s", tool_name, str(exc))
        raise RuntimeError(f"MCP tool call failed for `{tool_name}`: {str(exc)}") from exc


def list_tools(
    command: str,
    args: list[str] | None = None,
    env: dict[str, str] | None = None,
) -> list[str]:
    """
    Connect to an MCP server and return the available tool names.

    This sync wrapper keeps the rest of the project easy to read.
    """
    logger.info("Running synchronous MCP tool listing")
    return asyncio.run(list_tools_async(command=command, args=args, env=env))


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
    logger.info("Running synchronous MCP tool call for: %s", tool_name)
    return asyncio.run(
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

        logger.info("Created MCPClient for command: %s", command)

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
    try:
        config = get_default_filesystem_config() if root_path is None else build_filesystem_server_config(root_path)

        # TODO: Support HTTP MCP servers later if you want remote tool connections.
        logger.info("Creating filesystem MCP client")
        return MCPClient(
            command=config["command"],
            args=config["args"],
            env=config["env"],
        )
    except Exception as exc:
        logger.error("Failed to create filesystem MCP client: %s", str(exc))
        raise RuntimeError(f"Failed to create filesystem MCP client: {str(exc)}") from exc
