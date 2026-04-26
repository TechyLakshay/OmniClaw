# mcp/mcp_servers/calculator_server.py
from fastmcp import FastMCP

mcp = FastMCP("calculator")

@mcp.tool()
def add_numbers(a: float, b: float) -> str:
    """Add two numbers and return the result.
    return only that statement, no other text or explanation"""
    return str("the sum of " + str(a) + " and " + str(b) + " is " + str(a + b) + "any more questions, feel free to say master?")

@mcp.tool()
def get_current_time() -> str:
    """Return the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    mcp.run()  # runs over stdio by default