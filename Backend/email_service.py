"""
email_service.py

Gmail IMAP retrieval logic used by the frontend inbox.
Fetches all inbox emails and returns decoded subject, sender, date and body.
"""

import email
import imaplib
import re
from email.header import decode_header

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def _decode_mime_header(value: str) -> str:
    if not value:
        return ""

    decoded_parts = decode_header(value)
    decoded_string = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            decoded_string += part.decode(encoding or "utf-8", errors="replace")
        else:
            decoded_string += part

    return decoded_string


def _clean_text(value: str) -> str:
    if not value:
        return ""
    text = HTML_TAG_RE.sub(" ", value)
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _extract_body(msg) -> str:
    plain_body = ""
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            if "attachment" in content_disposition.lower():
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue

            decoded = payload.decode(part.get_content_charset() or "utf-8", errors="replace")

            if content_type == "text/plain" and not plain_body:
                plain_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html_body = decoded
            else:
                plain_body = decoded

    return _clean_text(plain_body or html_body)


def fetch_all_emails(gmail_address: str, app_password: str) -> list:

    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(gmail_address, app_password)
    mail.select("inbox")

    status, messages = mail.search(None, "ALL")
    if status != "OK":
        mail.logout()
        raise RuntimeError("Could not read inbox message IDs.")

    email_ids = messages[0].split()
    if not email_ids:
        mail.logout()
        return []

    emails = []

    for email_id in reversed(email_ids):
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        for response_part in msg_data:
            if not isinstance(response_part, tuple):
                continue

            msg = email.message_from_bytes(response_part[1])
            sender = _decode_mime_header(msg.get("From", ""))
            subject = _decode_mime_header(msg.get("Subject", "")) or "(No subject)"
            date = _decode_mime_header(msg.get("Date", ""))
            message_id = _decode_mime_header(msg.get("Message-ID", "")) or email_id.decode(errors="ignore")
            body = _extract_body(msg)[:5000]

            emails.append({
                "id": email_id.decode(errors="ignore"),
                "messageId": message_id,
                "from": sender,
                "subject": subject,
                "date": date,
                "body": body,
            })
            break

    mail.logout()
    return emails
