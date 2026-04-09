"""
send_generated_email.py

This script automatically sends generated emails ot a test inbox. 

Purpose of this file:
1. Uses the email_generator to create realistic emails
2. Sends them via Gmail SMTP
3. Simulate real inbox traffic (phishing + legitimate emails)
4. Helps test the PhishDefender system in a live enviroment
"""

import smtplib          # Used to send emails via SMTP
import time             # Used to add delay between emails 
import random           # Used to randomise timing
import os               # Used to access enviroment variables
from email.mime.text import MIMEText        # Used to foramt email content 
from email_generator import generate_emails # Email Generator 

# SMTP Configuration

# Gmail SMTP server settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # SSL secure port

# Sender email (this email sends emails indicated by ".sender")
SENDER_EMAIL = "phishdefender.sender@gmail.com"

# The app Password is loaded from an enviroment variable for security
SENDER_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
if not SENDER_APP_PASSWORD:
    raise ValueError("EMAIL_APP_PASSWORD enviroment variable not set")

# Receiver email 
RECEIVER_EMAIL = "phishdefender.test@gmail.com"

# Fucntoin - Send Single Email
def send_email(subject: str, body: str, display_from: str, label: str, category: str):
    """
    Send a single email using SMTP 
    Custom headers (X-Phish-*) are added for debugging / testing purposes
    """

    # Create email message
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = display_from
    msg["To"] = RECEIVER_EMAIL

    # Custom headers 
    msg["X-Phish-Label"] = label
    msg["X-Phish-Category"] = category

    # Connect to Gmail SMTP securly and send email
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.send_message(msg)

# Main Execution Function

def main():
    """
    Main Fucntion that:
    1. Generates a batch of emails
    2. Sends them one by one
    3. Adds random delay between sends

    This mimics real-world inbox behaviour rather than sending everything instantly
    """

    # Generates 20 emails (50% phishing, 50% legitimate)
    emails = generate_emails(count=20, balance=True)

    # Loop through each generated email
    for i, email in enumerate(emails, start=1):

        # Send email
        send_email (
            email["subject"],
            email["body"],
            email.get("display_from", SENDER_EMAIL),
            email["label"],
            email["category"]
        )

        # Print progress in terminal 
        print(f"Sent {i}: {email['label']} | {email['subject']} | {email.get('display_from')}")
        
        # Random delay between 5-20 seconds
        # This prevents emails arriving instantly and simulates real traffic
        time.sleep(random.randint(5, 20)) 

# Run Script
if __name__ == "__main__":
    main()