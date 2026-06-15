"""MCP server for password generation utilities."""

import random
import string
from fastmcp import FastMCP

mcp = FastMCP("password")


@mcp.tool()
def generate_password(length: int = 16, include_symbols: bool = True) -> str:
    """Generate a strong random password of given length."""
    chars = string.ascii_letters + string.digits
    if include_symbols:
        chars += "!@#$%^&*()-_=+"

    # guarantee at least one of each required type
    password = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
    ]
    if include_symbols:
        password.append(random.choice("!@#$%^&*()-_=+"))

    password += random.choices(chars, k=length - len(password))
    random.shuffle(password)

    return "".join(password)


@mcp.tool()
def check_password_strength(password: str) -> str:
    """Check how strong a given password is and explain why."""
    score = 0
    tips = []

    if len(password) >= 12:
        score += 1
    else:
        tips.append("use at least 12 characters")

    if any(c.isupper() for c in password):
        score += 1
    else:
        tips.append("add uppercase letters")

    if any(c.islower() for c in password):
        score += 1
    else:
        tips.append("add lowercase letters")

    if any(c.isdigit() for c in password):
        score += 1
    else:
        tips.append("add numbers")

    if any(c in "!@#$%^&*()-_=+" for c in password):
        score += 1
    else:
        tips.append("add symbols like !@#$")

    labels = {5: "Very Strong", 4: "Strong", 3: "Medium", 2: "Weak", 1: "Very Weak"}
    strength = labels.get(score, "Very Weak")

    if tips:
        return f"{strength} — to improve: {', '.join(tips)}."
    return f"{strength} — great password!"


if __name__ == "__main__":
    mcp.run()