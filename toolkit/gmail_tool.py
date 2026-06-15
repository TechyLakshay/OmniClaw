import base64
import html
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


@dataclass(slots=True)
class GmailEmail:
    """Normalized representation of a Gmail message."""

    id: str
    thread_id: str
    sender: str
    subject: str
    date: str
    snippet: str
    raw_body: str
    clean_body: str


def get_latest_unread_email() -> GmailEmail | None:
    """Fetch the latest unread Gmail message and normalize its contents."""
    logger.info("gmail_tool:get_latest_unread_email:start")
    service = _get_gmail_service()
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=1, q="is:unread")
        .execute()
    )

    messages = results.get("messages", [])
    if not messages:
        logger.info("gmail_tool:get_latest_unread_email:none_found")
        return None

    message_id = messages[0]["id"]
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    raw_body = _extract_body(payload).strip() or message.get("snippet", "")
    clean_body = _clean_email_text(raw_body, message.get("snippet", ""))

    email = GmailEmail(
        id=message["id"],
        thread_id=message.get("threadId", ""),
        sender=_get_header(headers, "From"),
        subject=_get_header(headers, "Subject"),
        date=_normalize_date(_get_header(headers, "Date")),
        snippet=message.get("snippet", ""),
        raw_body=raw_body,
        clean_body=clean_body,
    )
    logger.info(
        "gmail_tool:get_latest_unread_email:ready "
        f"id={email.id} subject_len={len(email.subject)} clean_body_len={len(email.clean_body)}"
    )
    return email


def mark_email_as_read(message_id: str) -> None:
    """Remove the UNREAD label from a Gmail message."""
    logger.info(f"gmail_tool:mark_email_as_read:start id={message_id}")
    service = _get_gmail_service()
    (
        service.users()
        .messages()
        .modify(userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]})
        .execute()
    )
    logger.info(f"gmail_tool:mark_email_as_read:done id={message_id}")


def remove_urls(text: str) -> str:
    """Strip all URLs from text."""
    return URL_PATTERN.sub("", text or "").strip()


def _get_gmail_service():
    creds = _load_credentials()
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _load_credentials() -> Credentials:
    token_path = os.getenv("GMAIL_TOKEN_FILE", "token.json")
    credentials_path = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")

    creds: Credentials | None = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as token_file:
            token_file.write(creds.to_json())
        return creds

    if creds and creds.valid:
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(token_path, "w", encoding="utf-8") as token_file:
        token_file.write(creds.to_json())
    return creds


def _get_header(headers: list[dict[str, Any]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return str(header.get("value", ""))
    return ""


def _extract_body(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body_data = payload.get("body", {}).get("data", "")

    if mime_type == "text/plain":
        return _decode_body(body_data)

    plain_parts = []
    html_parts = []
    for part in payload.get("parts", []):
        part_type = part.get("mimeType", "")
        content = _extract_body(part)
        if not content:
            continue
        if part_type == "text/plain":
            plain_parts.append(content)
        else:
            html_parts.append(content)

    if plain_parts:
        return "\n".join(plain_parts)
    if html_parts:
        return "\n".join(html_parts)
    return _decode_body(body_data)


def _decode_body(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return decoded.decode("utf-8", errors="ignore")


def _normalize_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.date().isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except Exception:
            return value


def _clean_email_text(body: str, snippet: str) -> str:
    text = body or snippet or ""
    if not text:
        return ""

    cleaned = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    cleaned = re.sub(r"(?is)<!--.*?-->", " ", cleaned)
    cleaned = re.sub(r"(?i)<br\s*/?>", "\n", cleaned)
    cleaned = re.sub(r"(?i)</p\s*>", "\n\n", cleaned)
    cleaned = re.sub(r"(?i)</div\s*>", "\n", cleaned)
    cleaned = re.sub(r"(?i)</li\s*>", "\n", cleaned)
    cleaned = re.sub(r"(?is)<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = remove_urls(cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n\s*\n\s*\n+", "\n\n", cleaned)
    cleaned = re.sub(r"\s*\n\s*", "\n", cleaned)
    cleaned = cleaned.strip()
    return cleaned if cleaned else remove_urls(snippet).strip()
