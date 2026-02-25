"""
email_service.py

email retrieval logic
connects to gmail via IMAP and extracts the most recent emails
"""

import imaplib
import email
from email.header import decode_header

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993

# Decodes MIME-encoded email headers (e.g UTF-8 encoded subjects)
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

"""
Connects to Gmail via IMAP and retreives the most recent emails
"""
def fetch_recent_emails(gmail_address: str, app_password: str, limit: int = 50) -> list:

    # Establish secure IMAP SSL connection
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

    # Login using app password 
    mail.login(gmail_address, app_password)

    # Select inbox folder
    mail.select("inbox")

    # Retrive all email IDs
    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    if not email_ids:
        mail.logout()
        return []
    
    # Get last N emails
    recent_ids = email_ids[-limit:]

    emails = []

    for email_id in recent_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                sender = _decode_mime_header(msg.get("From", ""))
                subject = _decode_mime_header(msg.get("Subject", ""))

                body = ""

                # Handle multipart emails
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))

                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            payload = part.get_payload(decode=True)
                            body = payload.decode(
                                part.get_content_charset() or "utf-8",
                                errors="replace"
                            )
                            break
                else:
                    payload = msg.get_payload(decode=True)
                    body = payload.decode(
                        msg.get_content_charset() or "utf-8",
                        errors="replace"
                    )
                
                emails.append({
                    "from": sender,
                    "subject": subject,
                    "body": body[:2000] # limit body length for saftey
                })
    
    mail.logout()
    return emails
