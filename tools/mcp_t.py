# tools/mcp_t.py
import asyncio
import json
import logging
import threading
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
from core.llm import invoke_llm

# avoid the mcp/ folder name clash — go up one level
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from mcp_tools.registry import MCP_SERVERS, get_server_for_tool

logger = logging.getLogger(__name__)

# ── async helpers ─────────────────────────────────────────────────────────────

async def _list_all_tools_async() -> list[dict]:
    all_tools = []
    for name, server in MCP_SERVERS.items():
        transport = PythonStdioTransport(server["args"][0])
        async with Client(transport) as client:
            tools = await client.list_tools()
            for t in tools:
                input_schema = getattr(t, "inputSchema", None)
                if input_schema is None:
                    input_schema = getattr(t, "input_schema", None)
                all_tools.append({
                    "server": name,
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": input_schema or {},
                })
    return all_tools

def _coerce_tool_result_to_text(result: Any) -> str:
    """Handle different FastMCP return shapes without hardcoding tool names."""
    if result is None:
        return ""
    if isinstance(result, str):
        return result
    if isinstance(result, (int, float, bool)):
        return str(result)
    if isinstance(result, list):
        parts = []
        for item in result:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts).strip()

    # FastMCP CallToolResult commonly has a `.content` field.
    content = getattr(result, "content", None)
    if isinstance(content, list):
        parts = []
        for item in content:
            text = getattr(item, "text", None)
            if text:
                parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts).strip()

    text = getattr(result, "text", None)
    if text:
        return str(text)

    if hasattr(result, "model_dump"):
        return json.dumps(result.model_dump(), ensure_ascii=False)
    return str(result)

async def _call_tool_async(tool_name: str, arguments: dict) -> str:
    server = get_server_for_tool(tool_name)
    if not server:
        return f"No MCP server found for tool: {tool_name}"
    transport = PythonStdioTransport(server["args"][0])
    async with Client(transport) as client:
        result = await client.call_tool(tool_name, arguments)
        return _coerce_tool_result_to_text(result)

# ── sync wrapper (thread-safe for FastAPI) ────────────────────────────────────

def _run_in_thread(coro):
    result_box = {}
    def target():
        try:
            result_box["v"] = asyncio.run(coro)
        except Exception as e:
            result_box["e"] = e
    t = threading.Thread(target=target, daemon=True)
    t.start()
    t.join()
    if "e" in result_box:
        raise result_box["e"]
    return result_box["v"]

def list_all_tools() -> list[dict]:
    return _run_in_thread(_list_all_tools_async())

def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    return _run_in_thread(_call_tool_async(tool_name, arguments))

# ── orchestrator entry point ──────────────────────────────────────────────────

_ROUTER_SYSTEM = """
You are a tool-calling router. The user sent a message.
Given these available MCP tools, decide which tool to call and what arguments to pass.
Respond ONLY in this JSON format with no extra text:
{{"tool": "<tool_name>", "arguments": {{"<key>": "<value>"}}}}
If no tool fits, respond: {{"tool": null, "arguments": {{}}}}
"""

def run_mcp_tool(message: str, history: list) -> str:
    try:
        tools = list_all_tools()
        tools_summary = "\n".join(
            f"- {t['name']}: {t['description']}\n  input_schema={json.dumps(t.get('input_schema', {}), ensure_ascii=False)}"
            for t in tools
        )
        prompt = f"Available tools:\n{tools_summary}\n\nUser message: {message}"
        raw = invoke_llm(prompt=prompt, system=_ROUTER_SYSTEM, history=[])
        raw_str = str(raw).strip()
        if raw_str.startswith("Error:"):
            logger.error(f"MCP router LLM failed: {raw_str}")
            return "MCP router failed."

        # Be tolerant if the model wraps JSON with extra text/code fences.
        json_start = raw_str.find("{")
        json_end = raw_str.rfind("}")
        if json_start == -1 or json_end == -1 or json_end <= json_start:
            logger.error(f"MCP router returned non-JSON output: {raw_str}")
            return "MCP router returned invalid response."

        parsed = json.loads(raw_str[json_start : json_end + 1])
        tool_name = parsed.get("tool")
        arguments = parsed.get("arguments", {})

        if not tool_name:
            logger.info("MCP router: no tool matched, falling back to chat")
            return invoke_llm(prompt=message, system="You are a helpful assistant.", history=history)

        logger.info(f"MCP calling tool={tool_name} args={arguments}")
        result = call_mcp_tool(tool_name, arguments)
        return f"[MCP → {tool_name}] {result}"

    except Exception as e:
        logger.error(f"run_mcp_tool error: {e}")
        return "MCP tool call failed."