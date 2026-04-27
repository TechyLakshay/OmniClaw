"""MCP client/runtime service.

This module centralizes MCP logic for the application:
1) discover tools from configured servers
2) ask the LLM to choose a tool + arguments
3) execute the selected MCP tool
4) normalize responses for chat output
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

from core.llm import invoke_llm
from local_mcp.registry import MCP_SERVERS, get_server_for_tool

logger = logging.getLogger(__name__)


_ROUTER_SYSTEM = """
You are a tool-calling router. The user sent a message.
Given these available MCP tools, decide which tool to call and what arguments to pass.
Use each tool's input_schema keys exactly.
Respond ONLY in this JSON format with no extra text:
{{"tool": "<tool_name>", "arguments": {{"<key>": "<value>"}}}}
If no tool fits, respond: {{"tool": null, "arguments": {{}}}}
"""


def _run_in_thread(coro: Any) -> Any:
    """Run async work from sync contexts safely."""
    result_box: dict[str, Any] = {}

    def target() -> None:
        try:
            result_box["value"] = asyncio.run(coro)
        except Exception as exc:  # noqa: BLE001
            result_box["error"] = exc

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join()

    if "error" in result_box:
        raise result_box["error"]
    return result_box.get("value")


def _coerce_tool_result_to_text(result: Any) -> str:
    """Handle different FastMCP result shapes without tool-specific hardcoding."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, (int, float, bool)):
        return str(result)
    if isinstance(result, list):
        parts = []
        for item in result:
            parts.append(str(getattr(item, "text", item)))
        return "\n".join(parts).strip()

    content = getattr(result, "content", None)
    if isinstance(content, list):
        parts = []
        for item in content:
            parts.append(str(getattr(item, "text", item)))
        return "\n".join(parts).strip()

    text = getattr(result, "text", None)
    if text:
        return str(text)

    if hasattr(result, "model_dump"):
        return json.dumps(result.model_dump(), ensure_ascii=False)
    return str(result)


async def _list_all_tools_async() -> list[dict[str, Any]]:
    """Collect tool metadata across all configured MCP servers."""
    all_tools: list[dict[str, Any]] = []
    for server_name, server in MCP_SERVERS.items():
        transport = PythonStdioTransport(server["args"][0])
        async with Client(transport) as client:
            tools = await client.list_tools()
            for tool in tools:
                input_schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None) or {}
                all_tools.append(
                    {
                        "server": server_name,
                        "name": tool.name,
                        "description": tool.description or "",
                        "input_schema": input_schema,
                    }
                )
    return all_tools


async def _call_tool_async(tool_name: str, arguments: dict[str, Any]) -> str:
    """Call a single MCP tool and return normalized text output."""
    server = get_server_for_tool(tool_name)
    if not server:
        return f"No MCP server found for tool: {tool_name}"

    transport = PythonStdioTransport(server["args"][0])
    async with Client(transport) as client:
        result = await client.call_tool(tool_name, arguments)
        return _coerce_tool_result_to_text(result)


def list_all_tools() -> list[dict[str, Any]]:
    """Public sync wrapper: list all available MCP tools."""
    return _run_in_thread(_list_all_tools_async())


def call_mcp_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Public sync wrapper: execute a single MCP tool by name."""
    return _run_in_thread(_call_tool_async(tool_name, arguments))


def run_mcp_tool(message: str, history: list[dict[str, Any]]) -> str:
    """Route a user message to MCP when appropriate and execute selected tool."""
    try:
        tools = list_all_tools()
        if not tools:
            logger.warning("MCP router: no tools discovered, falling back to chat")
            return invoke_llm(prompt=message, system="You are a helpful assistant.", history=history)

        tools_summary = "\n".join(
            f"- {tool['name']}: {tool['description']}\n  input_schema={json.dumps(tool['input_schema'], ensure_ascii=False)}"
            for tool in tools
        )
        prompt = f"Available tools:\n{tools_summary}\n\nUser message: {message}"
        raw = invoke_llm(prompt=prompt, system=_ROUTER_SYSTEM, history=[])
        raw_str = str(raw).strip()

        if raw_str.startswith("Error:"):
            logger.error("MCP router LLM failed: %s", raw_str)
            return "MCP router failed."

        json_start = raw_str.find("{")
        json_end = raw_str.rfind("}")
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            logger.error("MCP router returned non-JSON output: %s", raw_str)
            return "MCP router returned invalid response."

        parsed = json.loads(raw_str[json_start : json_end + 1])
        tool_name = parsed.get("tool")
        arguments = parsed.get("arguments", {})
        if not isinstance(arguments, dict):
            logger.error("MCP router returned non-dict arguments: %s", arguments)
            return "MCP router returned invalid tool arguments."

        if not tool_name:
            logger.info("MCP router: no tool matched, falling back to chat")
            return invoke_llm(prompt=message, system="You are a helpful assistant.", history=history)

        logger.info("MCP calling tool=%s args=%s", tool_name, arguments)
        result = call_mcp_tool(tool_name, arguments)
        return f"[MCP -> {tool_name}] {result}"

    except Exception as exc:  # noqa: BLE001
        logger.exception("run_mcp_tool error: %s", exc)
        return "MCP tool call failed."

