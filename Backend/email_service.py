"""
email_service.py

This file handles retreiving emails from Gmail using IMAP

What this file does:
1. Connects securly to Gmail using IMAP
2. Logs into the user's inbox using an App Password
3. Fetches emails from the inbox
4. Extracts and cleans:
    - sender
    - subject
    - date
    - body 
5. Supports:
    - fetching all emails 
    - fetching only new emails (based on UID)

Used by the backend (app.py) to supply emails for classification by the machine learning model. 
"""

import email                                # Used to parse raw email messages
import imaplib                              # Used to connect to Gmail via IMAP
import re                                   # Used for cleaning text (regex)
from email.header import decode_header      # Decodes encoded email headers

# Constants and Regex

# Gmail IMAP server details
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993 # Secure SSL port

# Regex patterns used to clean email content
HTML_TAG_RE = re.compile(r"<[^>]+>")    # Removes HTML tags
WHITESPACE_RE = re.compile(r"\s+")      # Normalises whitespace

# Helper Function - Decode MIME Headers

def _decode_mime_header(value: str) -> str:
    """
    Decode MIME-encoded email headers

    This function ensures it is converted into readable text
    """
    if not value:
        return ""

    decoded_parts = decode_header(value)
    decoded_string = ""

    for part, encoding in decoded_parts:
        if isinstance(part, bytes):
            # Decode bytes using detected encoding (fallback to UTF-8)
            decoded_string += part.decode(encoding or "utf-8", errors="replace")
        else:
            decoded_string += part

    return decoded_string

# Helper Fucntion - Clean Text

def _clean_text(value: str) -> str:
    """
    Clean email body text. 
    Removes:
    - Html tags
    - Excess whitespace

    returns a clean, readable string.
    """
    if not value:
        return ""
    text = HTML_TAG_RE.sub(" ", value)  # Remove HTML
    text = WHITESPACE_RE.sub(" ", text) # Normalise spaces
    return text.strip()

# Helper Function - Extract Email Body

def _extract_body(msg) -> str:
    """
    Extract the body from an email message

    Handles:
    - Multipart emails 
    - Single part emails 

    Priortiy:
    1. Plain text
    2. HTML

    Atachments are ignored
    """
    plain_body = ""

    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")

            # Skip attachments 
            if "attachment" in content_disposition.lower():
                continue

            payload = part.get_payload(decode=True)
            if payload is None:
                continue

            decoded = payload.decode(
                part.get_content_charset() or "utf-8",
                errors="replace"
            )
            
            # Prefer plain text if available
            if content_type == "text/plain" and not plain_body:
                plain_body = decoded
            elif content_type == "text/html" and not html_body:
                html_body = decoded
    else:
        # Handle non mupltipart emails
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode(
                msg.get_content_charset() or "utf-8",
                errors="replace"
            )
            if msg.get_content_type() == "text/html":
                html_body = decoded
            else:
                plain_body = decoded

    # Return cleaned text
    return _clean_text(plain_body or html_body)


# Main Function - Fetch Emails
def fetch_all_emails(
    gmail_address: str,
    app_password: str,
    only_after_uid: int | None = None
) -> list:
    """
    Fetch emails from a Gmail address

    Parameters:
    - gmail_address: user's Gmail address
    - app_password: Gmail App Password 
    - only_after_uid : if provided, only fetch emails newer than this UID

    Returns:
    A list of email dictionaries containing:
    - id / uid
    - messageId
    - from 
    - subject
    - date
    - body
    """

    # Connect to Gmail securely
    try:

        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        # Login using App Password
        mail.login(gmail_address, app_password)
        # Select inbox folder
        mail.select("inbox")

    except imaplib.IMAP4.error as e:
        error_text = str(e).upper()

        if "AUTHENTICATIONFAILED" in error_text or "INVALID CREDENTIALS" in error_text:
            raise ValueError ("Incorrect Gmail address or App Password.")
        
        raise ValueError("Unabkle to connect to Gmail.")
    
    except Exception:
        raise ValueError("Something went wrong while connecting to Gmail")

    try:
        # Search for emails 
        if only_after_uid is not None:
            # Fetch only emails newer than a given UID
            search_query = f"(UID {int(only_after_uid) + 1}:*)"
            status, messages = mail.uid("search", None, search_query)
        else:
            # Fetch all emails
            status, messages = mail.uid("search", None, "ALL")

        if status != "OK":
            raise RuntimeError("Could not read inbox message IDs.")

        uid_list = messages[0].split()
        if not uid_list:
            return []

        emails = []

        # Fetch each email (newest first)
        for uid_bytes in reversed(uid_list):
            uid_str = uid_bytes.decode(errors="ignore")

            status, msg_data = mail.uid("fetch", uid_str, "(RFC822)")
            if status != "OK":
                continue

            for response_part in msg_data:
                if not isinstance(response_part, tuple):
                    continue
                
                # Convert raw bytes into an email object
                msg = email.message_from_bytes(response_part[1])

                # Extract and decode feilds
                sender = _decode_mime_header(msg.get("From", ""))
                subject = _decode_mime_header(msg.get("Subject", "")) or "(No subject)"
                date = _decode_mime_header(msg.get("Date", ""))
                message_id = _decode_mime_header(msg.get("Message-ID", "")) or uid_str

                # Extract body (limited to avoid huge payloads)
                body = _extract_body(msg)[:5000]

                emails.append({
                    "id": uid_str,
                    "uid": int(uid_str),
                    "messageId": message_id,
                    "from": sender,
                    "subject": subject,
                    "date": date,
                    "body": body,
                })

                break # Only process first valid response part

        return emails

    finally:
        # Always close connection 
        mail.logout()