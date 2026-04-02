from email_generator import generate_emails

emails = generate_emails(5)

for e in emails:
    print("\n---")
    print(e["label"])
    print(e["subject"])
    print(e["body"])