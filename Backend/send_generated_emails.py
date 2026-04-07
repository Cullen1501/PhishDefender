import smtplib
import time
import random
import os
from email.mime.text import MIMEText
from email_generator import generate_emails


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SENDER_EMAIL = "phishdefender.sender@gmail.com"
SENDER_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
RECEIVER_EMAIL = "phishdefender.test@gmail.com"

def send_email(subject: str, body: str, display_from: str, label: str, category: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = display_from
    msg["To"] = RECEIVER_EMAIL

    msg["X-Phish-Label"] = label
    msg["X-Phish-Category"] = category

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)

def main():
    emails = generate_emails(count=20, balance=True)

    for i, email in enumerate(emails, start=1):
        send_email (
            email["subject"],
            email["body"],
            email.get("display_from", SENDER_EMAIL),
            email["label"],
            email["category"]
        )

        print(f"Sent {i}: {email['label']} | {email['subject']} | {email.get('display_from')}")
        
        time.sleep(random.randint(5, 20)) 


if __name__ == "__main__":
    main()