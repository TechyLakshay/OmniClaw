import argparse
import os

import httpx
from dotenv import load_dotenv


load_dotenv()


def send_message(gateway_url: str, secret_key: str, user_id: str, message: str) -> str:
    response = httpx.post(
        gateway_url,
        json={"user_id": user_id, "message": message},
        headers={"x-api-key": secret_key},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "No response returned.")


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI for OmniClaw")
    parser.add_argument(
        "message",
        nargs="*",
        help="Optional one-shot message. If omitted, interactive mode starts.",
    )
    parser.add_argument(
        "--user-id",
        default="cli-user",
        help="User id used for conversation history.",
    )
    parser.add_argument(
        "--gateway-url",
        default=os.getenv("CLI_GATEWAY_URL", "http://localhost:8000/chat"),
        help="Gateway /chat endpoint.",
    )
    args = parser.parse_args()

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise SystemExit("Missing SECRET_KEY in environment.")

    if args.message:
        prompt = " ".join(args.message).strip()
        if not prompt:
            raise SystemExit("Message cannot be empty.")
        try:
            reply = send_message(args.gateway_url, secret_key, args.user_id, prompt)
            print(reply)
        except httpx.HTTPError as exc:
            raise SystemExit(f"CLI request failed: {exc}") from exc
        return

    print("OmniClaw CLI started. Type 'exit' to quit.")
    while True:
        try:
            prompt = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting OmniClaw CLI.")
            break

        if not prompt:
            continue
        if prompt.lower() in {"exit", "quit"}:
            print("Exiting OmniClaw CLI.")
            break

        try:
            reply = send_message(args.gateway_url, secret_key, args.user_id, prompt)
            print(f"OmniClaw: {reply}")
        except httpx.HTTPError as exc:
            print(f"CLI request failed: {exc}")


if __name__ == "__main__":
    main()
