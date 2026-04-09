from Backend.email_generator import generate_emails

def main():
    email_count = 100
    preview_count = 10

    emails = generate_emails(count=email_count, balance=True)

    print(f"\nGenerated{len(emails)} emails.\n")
    print(f"showing first {preview_count} emails:\n")

    for i, email in enumerate(email[: preview_count], start=1):
        print("=" * 70)
        print(f"EMAIL {i}")
        print(f"Label   : {email['label']}")
        print(f"Category: {email['category']}")
        print(f"Style   : {email['style']}")
        print(f"Length  : {email['length']}")
        print(f"Subject :{email['subject']}\n")
        print(email["body"])
        print()

if __name__ == "__main__":
    main()