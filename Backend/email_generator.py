import random
import re
from datetime import datetime, timedelta
from typing import Dict, List

# =====================================
# HELPER DATA
# =====================================

NAMES = [
    "James", "Oliver", "George", "Harry", "Jack",
    "Noah", "Charlie", "Thomas", "Oscar", "William",
    "Amelia", "Olivia", "Isla", "Ava", "Emily",
    "Sophia", "Grace", "Lily", "Freya", "Evie",
    "Ethan", "Lucas", "Mason", "Logan", "Jacob",
    "Ella", "Mia", "Aria", "Zoe", "Chloe",
    "Daniel", "Henry", "Leo", "Sebastian", "Theo",
    "Hannah", "Lucy", "Ruby", "Jessica", "Sophie"
]

LEGIT_ORGS = [
    {
        "brand": "Oakridge Delivery",
        "domain": "oakridge-delivery.co.uk",
        "team_names": ["Delivery Team", "Customer Support", "Dispatch Team"]
    },
    {
        "brand": "ClearView Billing",
        "domain": "clearview-billing.co.uk",
        "team_names": ["Billing Team", "Accounts Department", "Customer Accounts"]
    },
    {
        "brand": "Campus Admin",
        "domain": "campus-admin.ac.uk",
        "team_names": ["Student Services", "Academic Registry", "IT Support"]
    },
    {
        "brand": "Horizon Support",
        "domain": "horizon-support.com",
        "team_names": ["Support Team", "Helpdesk", "Customer Services"]
    },
    {
        "brand": "NorthPoint Services",
        "domain": "northpoint-services.com",
        "team_names": ["Operations Team", "Service Desk", "Customer Services"]
    },
    {
        "brand": "BlueHarbour Utilities",
        "domain": "blueharbour-utilities.co.uk",
        "team_names": ["Customer Care", "Accounts Team", "Service Team"]
    }
]

PHISH_BRANDS = [
    "Account Protection Desk",
    "Secure Review Centre",
    "Billing Resolution Unit",
    "Access Verification Team",
    "Portal Recovery Service",
    "Security Check Office",
    "Document Access Centre",
    "Account Review Notice"
]

PHISH_DOMAINS = [
    "account-review-alert.net",
    "secure-login-check.com",
    "billing-verify-now.net",
    "portal-access-urgent.com",
    "security-centre-alert.net",
    "document-review-secure.com",
    "verify-account-office.net",
    "urgent-access-check.com"
]

MEETING_LOCATIONS = [
    "Room 2.14",
    "Conference Room A",
    "Conference Room B",
    "Main Office",
    "Reception Area",
    "Student Hub",
    "Lecture Theatre 3",
    "Seminar Room 1",
    "Online (Microsoft Teams)",
    "Online (Zoom)",
    "Hybrid - Main Office & Teams",
    "Building 5, Floor 2",
    "Training Room",
    "Admin Office",
    "Campus Library Meeting Room"
]

NEWSLETTER_TOPICS = [
    "service improvements",
    "upcoming maintenance",
    "new account features",
    "delivery updates",
    "security recommendations",
    "portal changes",
    "billing improvements"
]

PAYMENT_AMOUNTS = [
    "£4.99", "£12.50", "£19.99", "£42.00", "£87.35", "£129.99"
]

SHIPPING_ITEMS = [
    "your order", "your parcel", "your package",
    "your recent purchase", "your shipment"
]

FORMAL_GREETINGS = [
    "Dear {name},",
    "Hello {name},",
    "Good morning {name},",
    "Good afternoon {name},",
]

CASUAL_GREETINGS = [
    "Hi {name},",
    "Hello {name},",
    "Hi there,",
    "Morning {name},"
]

GENERIC_GREETINGS = [
    "Dear customer,",
    "Attention required,",
    "Notification,",
    "Hello,"
]

SIGNOFFS_FORMAL = [
    "Kind regards,",
    "Regards,",
    "Sincerely,",
    "Best regards,"
]

SIGNOFFS_NEUTRAL = [
    "Thank you,",
    "Thanks,",
    "Regards,",
    "Kind regards,"
]

PHISH_URGENCY = [
    "Urgent",
    "Immediate Action Required",
    "Important Notice",
    "Final Reminder",
    "Security Alert",
    "Action Needed"
]

PHISH_ACTIONS = [
    "verify your account",
    "confirm your identity",
    "review recent activity",
    "update your payment details",
    "reset your password",
    "restore account access",
    "reconfirm billing details"
]

PHISH_THREATS = [
    "to avoid temporary suspension",
    "to prevent interruption",
    "to avoid account restriction",
    "to prevent delayed access",
    "to avoid service disruption",
    "to keep your account active"
]

SHORT_TIME_LIMITS = [
    "within 24 hours",
    "today",
    "immediately",
    "within 12 hours",
    "before the end of the day"
]

STYLE_OPTIONS = ["formal", "casual", "system"]
LENGTH_OPTIONS = ["short", "medium", "long"]

# ===================================
# BASIC HELPERS
# ===================================

def random_date(days_back: int = 3, days_forward: int = 14) -> str:
    delta = random.randint(-days_back, days_forward)
    chosen_date = datetime.now() + timedelta(days=delta)
    return chosen_date.strftime("%d %B %Y")

def random_time() -> str:
    hour = random.randint(8, 17)
    minute = random.choice([0, 15, 30, 45])
    return f"{hour:02d}:{minute:02d}"

def random_ref(prefix: str = "REF") -> str:
    return f"{prefix}-{random.randint(100000, 999999)}"

def random_tracking() -> str:
    return f"TRK-{random.randint(100000, 999999)}"

def random_invoice() -> str:
    return f"INV-{random.randint(100000, 999999)}"

def random_ticket() -> str:
    return f"TKT-{random.randint(10000, 999999)}"

def choose_greeting(name: str, style: str) -> str:
    if style == "formal":
        return random.choice(FORMAL_GREETINGS).format(name=name)
    if style == "casual":
        return random.choice(CASUAL_GREETINGS).format(name=name)
    return random.choice(GENERIC_GREETINGS)

def choose_signoff(style: str) -> str:
    if style == "formal":
        return random.choice(SIGNOFFS_FORMAL)
    return random.choice(SIGNOFFS_NEUTRAL)

def maybe_add_line(lines: List[str], line: str, chance: float = 0.5) -> None:
    if random.random() < chance:
        lines.append(line)

def join_lines(lines: List[str]) -> str:
    cleaned = [line for line in lines if line and line.strip()]
    return "\n\n".join(cleaned)

def clean_name_for_email(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

def legit_sender(org: Dict[str, str]) -> str:
    local = random.choice([
        "support", "noreply", "accounts", "billing", "help",
        "notifications", "dispatch", "services", "admin"
    ])
    return f"{org['brand']} <{local}@{org['domain']}>"

def phish_sender() -> str:
    brand = random.choice(PHISH_BRANDS)
    local = random.choice(["security", "verify", "billing", "admin", "review", "support"])
    domain = random.choice(PHISH_DOMAINS)
    return f"{brand} <{local}@{domain}>"

def legit_link(org: Dict[str, str], path: str = "portal") -> str:
    return f"https://www.{org['domain']}/{path}/{random.randint(1000, 9999)}"

def phish_link(path: str = "portal") -> str:
    domain = random.choice(PHISH_DOMAINS)
    return f"http://{domain}/{path}/{random.randint(1000, 9999)}"

# ===============================================
# LEGITIMATE EMAIL BUILDERS
# ===============================================

def make_legit_shipping(style: str, length: str) -> Dict[str, str]:
    org = random.choice([o for o in LEGIT_ORGS if "Delivery" in o["brand"] or "Services" in o["brand"]])
    name = random.choice(NAMES)
    item = random.choice(SHIPPING_ITEMS)

    subjects = [
        f"{org['brand']}: Dispatch confirmation",
        f"{org['brand']}: Your delivery is on the way",
        f"{org['brand']}: Shipment update",
        f"{org['brand']}: Delivery status update"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            f"We are pleased to confirm that {item} has now been dispatched.",
            f"This is to let you know that {item} is currently in transit.",
            f"Your delivery has now been processed and is on the way."
        ]),
        f"Tracking number: {random_tracking()}",
        f"Estimated delivery date: {random_date(0, 7)}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"You can review the latest delivery status here:\n{legit_link(org, 'tracking')}", 0.85)

    if length == "long":
        maybe_add_line(lines, "Please keep this reference for your records.", 0.8)

    lines.extend([
        choose_signoff(style),
        random.choice(org["team_names"]),
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "shipping_update",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_meeting(style: str, length: str) -> Dict[str, str]:
    org = random.choice([o for o in LEGIT_ORGS if ".ac.uk" in o["domain"] or "Support" in o["brand"]])
    name = random.choice(NAMES)
    location = random.choice(MEETING_LOCATIONS)

    subjects = [
        "Meeting reminder",
        "Upcoming meeting notification",
        "Scheduled meeting update",
        "Appointment reminder"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "This is a reminder regarding your upcoming meeting.",
            "You have a scheduled meeting coming up.",
            "Please note that your meeting is due soon."
        ]),
        f"Date: {random_date(0, 10)}",
        f"Time: {random_time()}",
        f"Location: {location}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Reference: {random_ref()}", 0.75)

    lines.extend([
        choose_signoff(style),
        random.choice(org["team_names"]),
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "meeting_reminder",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_invoice(style: str, length: str) -> Dict[str, str]:
    org = random.choice([o for o in LEGIT_ORGS if "Billing" in o["brand"] or "Utilities" in o["brand"] or "Services" in o["brand"]])
    name = random.choice(NAMES)

    subjects = [
        f"{org['brand']}: Invoice available",
        f"{org['brand']}: Payment receipt",
        f"{org['brand']}: Billing confirmation",
        f"{org['brand']}: Transaction summary"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "Your latest invoice is now available.",
            "This email confirms your recent payment.",
            "Please find your billing summary below."
        ]),
        f"Invoice number: {random_invoice()}",
        f"Amount: {random.choice(PAYMENT_AMOUNTS)}",
        f"Date issued: {random_date(5, 0)}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Billing portal:\n{legit_link(org, 'billing')}", 0.8)

    if length == "long":
        maybe_add_line(lines, "If you believe this has been issued in error, please contact the billing team.", 0.8)

    lines.extend([
        choose_signoff(style),
        random.choice(org["team_names"]),
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "invoice_receipt",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_newsletter(style: str, length: str) -> Dict[str, str]:
    org = random.choice(LEGIT_ORGS)
    topic_a = random.choice(NEWSLETTER_TOPICS)
    topic_b = random.choice([t for t in NEWSLETTER_TOPICS if t != topic_a])

    subjects = [
        f"{org['brand']} monthly update",
        f"{org['brand']} service newsletter",
        f"Latest updates from {org['brand']}",
        f"{org['brand']} customer update"
    ]

    lines = [
        choose_greeting(random.choice(NAMES), style),
        f"Welcome to the latest update from {org['brand']}.",
        f"In this edition, we cover {topic_a} and {topic_b}."
    ]

    if length in ["medium", "long"]:
        lines.append(random.choice([
            "We are continuing to improve the overall service experience.",
            "Additional improvements will be introduced over the coming weeks.",
            "Further changes may be announced in a future update."
        ]))

    if length == "long":
        lines.append(f"Manage your preferences here:\n{legit_link(org, 'preferences')}")

    lines.extend([
        choose_signoff(style),
        "Communications Team",
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "newsletter",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_support_reply(style: str, length: str) -> Dict[str, str]:
    org = random.choice(LEGIT_ORGS)
    name = random.choice(NAMES)

    subjects = [
        f"{org['brand']}: Support ticket update",
        f"{org['brand']}: Case response",
        f"{org['brand']}: Request received",
        f"{org['brand']}: Ticket status",
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "Thank you for contacting support.",
            "We have received your request.",
            "Your support query has now been logged."
        ]),
        f"Ticket ID: {random_ticket()}",
        random.choice([
            "A member of the team will review your request shortly.",
            "Your case is currently under review.",
            "We will provide an update as soon as more information is available."
        ])
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "Please reply to this email if you need to provide any additional information.", 0.8)

    if length == "long":
        maybe_add_line(lines, f"Support portal:\n{legit_link(org, 'support')}", 0.75)

    lines.extend([
        choose_signoff(style),
        random.choice(org["team_names"]),
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "support_reply",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_password_reset_confirmation(style: str, length: str) -> Dict[str, str]:
    org = random.choice(LEGIT_ORGS)
    name = random.choice(NAMES)

    subjects = [
        f"{org['brand']}: Password reset confirmation",
        f"{org['brand']}: Security update complete",
        f"{org['brand']}: Credentials changed"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "This confirms that your password was changed successfully.",
            "Your account credentials have been updated.",
            "The recent password reset request has now been completed."
        ]),
        f"Date: {random_date(3, 0)}",
        f"Reference: {random_ref()}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "If you did not make this change, contact support immediately.", 0.85)

    lines.extend([
        choose_signoff(style),
        "Security Team",
        org["brand"]
    ])

    return {
        "label": "legitimate",
        "category": "password_reset_confirmation",
        "display_from": legit_sender(org),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

# ===================================================
# PHISHING EMAIL BUILDERS
# ===================================================

def make_phish_account_verification(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(PHISH_BRANDS)
    name = random.choice(NAMES)

    subjects = [
        f"{random.choice(PHISH_URGENCY)}: verify your account",
        f"{random.choice(PHISH_URGENCY)}: access issue detected",
        "Security notice",
        "Account review required"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            f"We noticed unusual activity on your account.",
            f"A recent login attempt could not be verified.",
            f"Your account access has been flagged for additional review."
        ]),
        f"Please {random.choice(PHISH_ACTIONS)} {random.choice(SHORT_TIME_LIMITS)} {random.choice(PHISH_THREATS)}.",
        f"Review now:\n{phish_link('verify')}"
    ]

    if length == "long":
        maybe_add_line(lines, f"Case reference: {random_ref()}", 0.8)

    lines.extend([
        choose_signoff(style),
        brand
    ])

    return {
        "label": "phishing",
        "category": "account_verification",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_delivery_problem(style: str, length: str) -> Dict[str, str]:
    name = random.choice(NAMES)

    subjects = [
        "Delivery failed - action required",
        "Parcel on hold",
        "Address issue detected",
        f"{random.choice(PHISH_URGENCY)}: delivery could not be completed"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "We were unable to complete your delivery due to missing address information.",
            "Your parcel has been placed on hold pending address confirmation.",
            "A delivery issue was detected and action is required."
        ]),
        f"Tracking number: {random_tracking()}",
        f"Update details here:\n{phish_link('delivery')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Please respond {random.choice(SHORT_TIME_LIMITS)} to prevent return to sender.", 0.9)

    lines.extend([
        choose_signoff(style),
        random.choice(PHISH_BRANDS)
    ])

    return {
        "label": "phishing",
        "category": "delivery_problem",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_password_expiry(style: str, length: str) -> Dict[str, str]:
    subjects = [
        "Password expires today",
        "Credential expiry warning",
        f"{random.choice(PHISH_URGENCY)}: password update needed",
        "Access restoration required"
    ]

    lines = [
        choose_greeting(random.choice(NAMES), style),
        random.choice([
            "Your password is due to expire today.",
            "Your current credentials require immediate renewal.",
            "A password reset is required to maintain access."
        ]),
        f"Reset now:\n{phish_link('reset')}",
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Failure to act may result in account restriction.", 0.9)

    if length == "long":
        maybe_add_line(lines, f"Ticket number: {random_ticket()}", 0.65)

    lines.extend([
        choose_signoff(style),
        "IT Helpdesk"
    ])

    return {
        "label": "phishing",
        "category": "password_expiry",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_document_share(style: str, length: str) -> Dict[str, str]:
    name = random.choice(NAMES)

    subjects = [
        f"{name}, a document has been shared with you",
        "Secure file available",
        "Restricted document access",
        f"{random.choice(PHISH_URGENCY)}: file waiting review"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "A protected document has been shared with your account.",
            "You have received a secure file that requires review.",
            "A confidential attachment is waiting for your confirmation."
        ]),
        f"Open file:\n{phish_link('document')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Access expires on {random_date(0, 3)}.", 0.9)

    if length == "long":
        maybe_add_line(lines, "Sign in to continue viewing the document.", 0.8)

    lines.extend([
        choose_signoff(style),
        random.choice(PHISH_BRANDS)
    ])

    return {
        "label": "phishing",
        "category": "document_share",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_payment_issue(style: str, length: str) -> Dict[str, str]:
    name = random.choice(NAMES)

    subjects = [
        "Payment method declined",
        f"{random.choice(PHISH_URGENCY)}: billing problem detected",
        "Subscription interruption notice",
        "Outstanding payment confirmation required"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "We were unable to process your latest payment method.",
            "A billing issue has been detected on your account.",
            "Your subscription may be interrupted due to a failed payment check."
        ]),
        f"Amount pending: {random.choice(PAYMENT_AMOUNTS)}",
        f"Update payment details:\n{phish_link('billing')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Please review this {random.choice(SHORT_TIME_LIMITS)}.", 0.85)

    lines.extend([
        choose_signoff(style),
        random.choice(PHISH_BRANDS)
    ])

    return {
        "label": "phishing",
        "category": "payment_issue",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_university_portal(style: str, length: str) -> Dict[str, str]:
    name = random.choice(NAMES)

    subjects = [
        "Student portal verification required",
        "Course access alert",
        "Assessment access problem",
        f"{random.choice(PHISH_URGENCY)}: portal login issue"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "We could not verify your recent portal session.",
            "Your student access requires reconfirmation.",
            "A login issue has been detected against your student profile."
        ]),
        f"Continue here:\n{phish_link('student-login')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "Failure to verify may result in temporary portal interruption.", 0.9)

    lines.extend([
        choose_signoff(style),
        "Student Services"
    ])

    return {
        "label": "phishing",
        "category": "university_portal_warning",
        "display_from": phish_sender(),
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

# =============================================
# BUILDER COLLECTIONS
# =============================================

LEGIT_BUILDERS = [
    make_legit_shipping,
    make_legit_meeting,
    make_legit_invoice,
    make_legit_newsletter,
    make_legit_support_reply,
    make_legit_password_reset_confirmation,
]

PHISH_BUILDERS = [
    make_phish_account_verification,
    make_phish_delivery_problem,
    make_phish_password_expiry,
    make_phish_document_share,
    make_phish_payment_issue,
    make_phish_university_portal,
]

# ======================================
# MASTER GENERATOR
# ======================================

def generate_email(force_label: str = None) -> Dict[str, str]:
    style = random.choice(STYLE_OPTIONS)
    length = random.choice(LENGTH_OPTIONS)

    if force_label == "legitimate":
        builder = random.choice(LEGIT_BUILDERS)
    elif force_label == "phishing":
        builder = random.choice(PHISH_BUILDERS)
    else:
        builder = random.choice(PHISH_BUILDERS if random.random() < 0.5 else LEGIT_BUILDERS)

    email = builder(style, length)
    email["style"] = style
    email["length"] = length
    return email

def generate_emails(count: int = 100, balance: bool = True) -> List[Dict[str, str]]:
    emails = []

    if balance:
        half = count // 2
        for _ in range(half):
            emails.append(generate_email("legitimate"))
            emails.append(generate_email("phishing"))

        if count % 2 == 1:
            emails.append(generate_email())
    else:
        for _ in range(count):
            emails.append(generate_email())

    random.shuffle(emails)
    return emails