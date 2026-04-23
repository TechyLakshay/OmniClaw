import logging

from tools.file_writer import write_file


logger = logging.getLogger(__name__)


def save_email_summary(email_data: dict, summary: str) -> str:
    """Save a compact email summary to the notes directory."""
    subject = email_data.get("subject") or "email_summary"
    safe_subject = _slugify(subject)[:50] or "email_summary"

    content = "\n".join(
        [
            "# Email Summary",
            "",
            f"**From:** {email_data.get('from', '')}",
            f"**Subject:** {email_data.get('subject', '')}",
            f"**Date:** {email_data.get('date', '')}",
            "",
            "## Summary",
            "",
            summary,
        ]
    )

    logger.info(
        f"file_saver:save:start message_id={email_data.get('id', '')} filename=email_{safe_subject}"
    )
    status = write_file(f"email_{safe_subject}", content)
    logger.info(f"file_saver:save:done status={status}")
    return status


def _slugify(value: str) -> str:
    chars = []
    for char in value.lower():
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-", "_"}:
            chars.append("_")
    return "".join(chars).strip("_")
