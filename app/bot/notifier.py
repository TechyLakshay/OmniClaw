import logging
import os

import httpx


logger = logging.getLogger(__name__)


def send_high_priority_notification(sender: str, subject: str, summary: str) -> str:
    """Send a high-priority Telegram notification."""
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token:
        raise RuntimeError("Missing TELEGRAM_TOKEN")
    if not chat_id:
        raise RuntimeError("Missing TELEGRAM_CHAT_ID")

    message = (
        "🚨 New Email\n"
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"Summary: {summary}"
    )
    logger.info(f"notifier:send:start chat_id={chat_id} text_len={len(message)}")
    response = httpx.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=30,
    )
    response.raise_for_status()
    logger.info(f"notifier:send:done status_code={response.status_code}")
    return "Telegram notification sent."
