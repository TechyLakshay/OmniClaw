"""Example MCP server with simple calculator utilities.

This file is intentionally small so it is easy to understand and extend.
"""

from fastmcp import FastMCP

mcp = FastMCP("calculator")


@mcp.tool()
def add_numbers(a: float, b: float) -> str:
    """Add two numbers and return a concise human-readable result."""
    total = a + b
    return f"The sum of {a} and {b} is {total}."


@mcp.tool()
def get_current_time() -> str:
    """Return the local date and time in a simple format."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # Runs over stdio by default, which is what FastMCP client expects.
    mcp.run()