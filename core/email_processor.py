import logging
import re
import time
from typing import TypedDict

from core.llm import invoke_llm
from integrations.file_saver import save_email_summary
from tools.gmail_tool import get_latest_unread_email, mark_email_as_read


logger = logging.getLogger(__name__)
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


class EmailProcessResult(TypedDict, total=False):
    status: str
    summary: str
    file_status: str
    marked_as_read: bool
    email: dict
    message: str


SUMMARY_SYSTEM = """Summarize this email in at most 2 short lines.
Rules:
- No links
- No marketing language
- Output plain text only
"""


def process_latest_unread_email(mark_as_read: bool = False) -> EmailProcessResult:
    """Fetch the latest unread email, summarize it, and save it to notes."""
    total_start = time.perf_counter()
    logger.info(f"email_processor:start mark_as_read={mark_as_read}")

    try:
        email = get_latest_unread_email()
        if not email:
            return {"status": "no_unread_email", "message": "No unread email found."}

        summary = summarize_email(email.sender, email.subject, email.date, email.clean_body)
        file_status = save_email_summary(
            {
                "id": email.id,
                "from": email.sender,
                "subject": email.subject,
                "date": email.date,
                "clean_body": email.clean_body,
            },
            summary,
        )

        if mark_as_read:
            mark_email_as_read(email.id)

        logger.info(
            f"email_processor:success id={email.id} total_elapsed={time.perf_counter() - total_start:.2f}s"
        )
        return {
            "status": "success",
            "summary": summary,
            "file_status": file_status,
            "marked_as_read": mark_as_read,
            "email": {
                "id": email.id,
                "from": email.sender,
                "subject": email.subject,
                "date": email.date,
                "clean_body": email.clean_body,
            },
        }
    except Exception as exc:
        logger.exception("email_processor:error")
        return {"status": "error", "message": str(exc)}


def summarize_email(sender: str, subject: str, date: str, clean_body: str) -> str:
    """Create a short, cleaned summary for the latest unread email."""
    prompt = "\n".join(
        [
            f"From: {sender}",
            f"Subject: {subject}",
            f"Date: {date}",
            "",
            "Email body:",
            clean_body[:4000],
        ]
    )
    summary = invoke_llm(prompt=prompt, system=SUMMARY_SYSTEM, history=[]).strip()
    summary = URL_PATTERN.sub("", summary)
    lines = [line.strip(" -*\t") for line in summary.splitlines() if line.strip()]
    if not lines:
        return "No clear summary available."
    return "\n".join(lines[:2])
