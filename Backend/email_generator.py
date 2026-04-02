import random 
import re
from datetime import datetime, timedelta
from typing import Dict, List

# =====================================
# HELPER DATA
# =====================================

NAMES = [
    "Steven", "Alex", "Sam", "Jordan", "Taylor",
    "Jamie", "Morgan", "Casey", "Riley", "Avery"
]

FAKE_BRANDS = [
    "SecureBank", "QucikShip", "CloudBox", "UniPortal",
    "DataSafe", "NetAssist", "PayFriend", "StudentHub",
    "ParcelPoint", "WorkFlow Central"
]

DEPARTMENTS = [
    "Support Team", "Security Team", "Accounts Department",
    "IT Helpdesk", "Customer Services", "Student Services",
    "Billing Team", "Delivery Team", "Access Team"
]

MEETING_LOCATIONS = [
    "Room 2.14", "Main Office", "Online", "Teams",
    "Conference Room B", "Student Hub", "Reception Area"
]

NEWSLETTER_TOPICS = [
    "service improvments",
    "upcoming maintenance",
    "new account features",
    "delivery updates",
    "security recommendations",
    "portal changes",
    "billing improvemnts"
]

PAYMENT_AMOUNTS = [
    "£4.99", "£12.50", "£19.99", "£42.00", "£87.35", "£129.99"
]

SHIPPING_ITEMS = [
    "your order", "your parcel", "your package",
    "your recent purchase", "your shipment"
]

FORMAL_GREETINGS = [
    "Dear {name}",
    "Hello {name}",
    "Good morning {name}",
    "Good afternoon {name}",
]

CASUAL_GREETINGS = [
    "Hi {name}",
    "Hello,",
    "Hi there,",
    "Morning {name}"
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
    "Best Regards,"
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
    "confirm your identify",
    "review recent activity",
    "upadate your payment details",
    "reset your password",
    "restore account access",
    "reconfirm billing details"
]

PHISH_THREATS = [ 
    "to avoid temporary suspension",
    "to prevent interuption",
    "to avoid account restriction",
    "to prevent delayed access",
    "to avoid service disruption",
    "to keep your acount active"
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

def fake_domain(brand: str) -> str:
    clean = re.sub(r"[^a-z0-9]", "", brand.lower())
    return f"{clean}.local"

def fake_link(brand: str, path: str = "portal") -> str:
    return f"http://{fake_domain(brand)}/{path}/{random.randint(1000, 9999)}"

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

def join_lines(lines: List[str])-> str:
    cleaned = [line for line in lines if line and line.strip()]
    return "\n\n".join(cleaned)

# ===============================================
# LEGITIMATE EMAIL BIULDERS
# ===============================================

def make_legit_shipping(style: str, length: str) -> Dict [str, str]:
    brand =random.choice(FAKE_BRANDS)
    name = random.choice(NAMES)
    item = random.choice(SHIPPING_ITEMS)

    subjects = [
        f"{brand}: Dispatch confirmation",
        f"{brand}: Your delivery is on the way",
        f"{brand}: Shipment update",
        f"{brand}: Delivery status update"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            f"We are pleased to confirm that {item} has now been dispatched."#
            f"This is to let you know that {item} is currently in transit."
            f"Your delivery has now been processed and is on the way."
        ]),

        f"Tracking number: {random_tracking()}",
        f"Estimated delivery date: {random_date(0, 7)}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"You can review the latest delivery status here:\n{fake_link(brand, 'tracking')}", 0.75)

    if length == "long":
        maybe_add_line(lines, "Plesae keep this refernce for your records.", 0.8)
    
    lines.extend([
        choose_signoff(style),
        f"{brand} Delkivery Team"
    ])

def make_legit_meeting(style: str, length: str) -> Dict[str, str]:
    name = random.choice(NAMES)
    location = random.choice(MEETING_LOCATIONS)

    subjects = [
        "Meeting reminder",
        "Upcoming meeting notifcation",
        "Scheduled meeting update",
        "Appointment reminder"
    ]

    lines = [
        choose_greeting(name,style),
        random.choice([
            "This is a reminder regarding your upcoming meeting.",
            "you have a scheduled meeting coming up.",
            "Please note that your meeting is due soon."
        ]),

        f"Date: {random_date(0, 10)}",
        f"Time: {random_time()}",
        f"Location: {location}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Reference: {random_ref()}", 0.7)
    
    lines.extend([
        choose_signoff(style),
        random.choice(DEPARTMENTS)
    ])

    return {
        "label": "legitimate", 
        "category": "meeting_reminder",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_invoice(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)
    name = random.choice(NAMES)

    subjects = [
        f"{brand}: Invoice available",
        f"{brand}: Payment receipt",
        f"{brand}: Billing confirmation",
        f"{brand}: Transaction summary"
    ]

    lines = [
        choose_greeting(name,style),
        random.choice([
            "Your lateset invoice is now available.",
            "This email confirms your recent payment.",
            "Please find your billing summary below."
        ]),

        f"Invoice number: {random_invoice()}",
        f"Amount: {radnom.choice(PAYMENT_AMOUNTS)}",
        f"Date issued: {random_date(5, 0)}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Billing portal:\n{fake_link(brand, 'billing')}, 0.7")

    if length == "long":
        maybe_add_line(lines, "If you belive this has been issued in error, please contact the billing team.", 0.8)

    lines.extend([
        choose_signoff(style),
        f"{brand} Billing Team"
    ])

    return {
        "label": "legitimate",
        "category": "invoice_recepit",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_newsletter(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)
    topic_a = random.choice(NEWSLETTER_TOPICS)
    topic_b = random.choice([ t for t in NEWSLETTER_TOPICS if t != topic_a])


    subjects = [
        f"{brand} monthly update",
        f"{brand} service newsletter",
        f"Latest updates from {brand}",
        f"{brand} customer update"
    ]

    lines = [
        choose_greeting(random.choice(NAMES), style),
        f"Welcome to the latest update from {brand}.",
        f"In thsi edition, we cover {topic_a} and {topic_b}."
    ]

    if length in ["medium", "long"]:
        lines.append(random.choice([
            "We are continuing to imporve the overall service experience.",
            "Additional imporvments will be introduced over the coming weeks.",
            "Further changes may be announced in a future update."
        ]))

    if length == "long":
        lines.append(f"Manage your preferences here:\n{fake_link(brand, 'preferences')}")

    lines.extend([
        choose_signoff(style),
        f"{brand} Communications"
    ])

    return {
        "label": "legitimate",
        "category": "newsletter",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_support_reply(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)
    name = random.choice(NAMES)

    subjects = [
        f"{brand}: Support ticket update",
        f"{brand}: Case response",
        f"{brand}: Request received",
        f"{brand}: Ticket Status",
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
            "We will provide an upadte as sonn as more information is available." 
        ])     
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "Please reply to this email if you need to provide any additional information.", 0.75)

    if length == "long": 
        maybe_add_line(lines, f"Support portal:\n{fake_link(brand, 'support')}", 0.7)
    
    lines.extend([
        choose_signoff(style),
        f"{brand} Support Team"
    ])

    return {
        "label": "legitimate",
        "category": "support_reply",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_legit_password_reset_confirmation(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)
    name = random.choice(NAMES)

    subjects = [
        f"{brand}: Password reset confirmation",
        f"{brand}: Security update complete",
        f"{brand}: Credentials changed"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "This confrims that your password was changed successfully.",
            "Your account credentials have neemn updated.",
            "The recent password reset request has now been completed."
        ]),
        f"Date: {random_date(3, 0)}",
        f"Reference: {random_ref()}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "If you did not make this change, contact support immediatly.", 0.8)

    lines.extend([
        choose_signoff(style),
        f"{brand} Security Team"
    ])

    return {
        "label": "legitimate",
        "category": "password_reset_confimation",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

# ===================================================
# PHISHING_STYLE EMAIL BIULDERS
# Safe synthetic content only using fake brand, fake domains
# ===================================================

def make_phish_account_verification(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)
    name = random.choice(NAMES)

    subjects = [
        f"{random.choice(PHISH_URGENCY)}: verify your {brand} account",
        f"{random.choice(PHISH_URGENCY)}: {brand} access issue",
        f"{brand} security notice"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            f"We noticed unusal activity on your {brand} account.",
            f"A recent login attempt could not be verified on yout {brand} profile.",
            f"Your {brand} access has been flagged for additional review."
        ]),
        f"Please {random.choice(PHISH_ACTIONS)} {random.choice(SHORT_TIME_LIMITS)} {random.choice(PHISH_THREATS)}.",
        f"Review now:\n{fake_link(brand, 'verify')}"
    ]

    if length == "long":
        maybe_add_line(lines, f"Case refernce: {random_ref()}", 0.8)

    lines.extend([
        choose_signoff(style),
        f"{brand} Security Team"
    ])

    return {
        "label": "phishing",
        "category": "account_verification",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_delivery_problem(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(["QuickShip", "ParcelPoint", "DeliveryDesk", "ShipTrack"])
    name = random.choice(NAMES)

    subjects = [
        "Delivery faild -action reuqired",
        "Parcel on hold",
        "Address issue detected",
        f"{random.choice(PHISH_URGENCY)}: delivery could not be completed"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "WE were unable to complete your delivery due to missing address infromation.",
            "Your parcel hs been placed on hold pending address confirmation.",
            "A delivery issue was detected and action is required."
        ]),
        f"Tracking number: {random_tracking()}",
        f"Update details here:\n{fake_link(brand, 'delivery')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, F"Please respond {random.choice(SHORT_TIME_LIMITS)} to prevent return to sender.", 0.9)
    
    lines.extend([
        choose_signoff(style),
        f"{brand} Delivery Team"
    ])

    return {
        "label": "phishing",
        "category": "delivery_problem",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_password_expery(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(FAKE_BRANDS)

    subjects = [
        "Password expires today",
        "Credential expiry warning",
        f"{random.choice(PHISH_URGENCY)}: password update needed",
        "Access restoration required"
    ]

    lines = [
        choose_greeting(random.choice(NAMES), style),
        random.choice([
            f"Your {brand} password is due to expier today.",
            f"Your current credentials for {brand} require immediate renewal.",
            "A password reset is required to maintain access."
        ]),

        f"Reset now:\n{fake_link(brand, 'reset')}",
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Faliure to act {random.choice(PHISH_THREATS)}.", 0.85)
    
    if length == "long":
        maybe_add_line(lines, f"Ticket number: {random_ticket()}", 0.6)
    
    lines.extend([
        choose_signoff(style),
        "IT Helpdesk"
    ])

    return {
        "label": "phishing",
        "category": "password_expiry",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_document_share(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(["CloudBox", "DocuFlow", "SharePoint Secure", "WorkFlow Central"])
    name = random.choice(NAMES)

    subjects = [
        f"{name}, a document has been shared wiht you",
        "Secure file available",
        "Restricted document access",
        f"{random.choice(PHISH_URGENCY)}: file waiting review"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "A protected document has been chared wiht you account.",
            "You have recived a secure file that requires review.",
            "A confidential attachment is waiting for your confirmation."
        ]),
        f"Open file:\n{fake_link(brand, 'document')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Access expires on {random_date(0, 3)}.", 0.9)
    
    if length == "long":
        maybe_add_line(lines, "Sign in to coninue viewing the document.", 0.8)
    
    lines.extend([
        choose_signoff(style),
        f"{brand} Access Team"
    ])

    return {
        "label": "phishing",
        "category": "document_share",
        "subject": "document_share",
        "body": join_lines(lines)
    }

def make_phish_payment_issue(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(["PayFriend", "BillingDesk", "SecureBank", "AccountPay"])
    name = random.choice(NAMES)

    subjects = [
        "payment method declined",
        f"{random.choice(PHISH_URGENCY)}: billing problem detected",
        "Subscription interruption notice",
        "Outstanding payment confimation required"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "We were unable to process your latest payment method.",
            "A billing issue has been detected on your account.",
            "Your subscription may be interrupted due to a failed payment check."
        ]),
        f"Amount pending: {random.choice(PAYMENT_AMOUNTS)}",
        f"Update payment details:\n{fake_link(brand, 'biling')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, f"Please review this {random.choice(SHORT_TIME_LIMITS)}.", 0.8)

    lines.extend([
        choose_signoff(style),
        f"{brand} Accounts Department"
    ])

    return {
        "label": "phishing",
        "category": "payment_issue",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

def make_phish_university_portal(style: str, length: str) -> Dict[str, str]:
    brand = random.choice(["UniPortal", "StudentHub", "Campus Access", "Exam Services"])
    name = random.choice(NAMES)

    subjects = [
        "Student portal verification reuqired",
        "Course access alert",
        "Assessment acees problem",
        f"{random.choice(PHISH_URGENCY)}: portal login issue"
    ]

    lines = [
        choose_greeting(name, style),
        random.choice([
            "We could not verify your recent portal session.",
            "Your student access reqires reconfirmation.",
            "A login issue has been detected against your student profile."
        ]),
        f"COntinue here:\n{fake_link(brand, 'student-login')}"
    ]

    if length in ["medium", "long"]:
        maybe_add_line(lines, "Faliure to verify may result in temporary portal interruption.", 0.85)

    lines.extend([
        choose_signoff(style),
        f"{brand} Student Services"
    ])

    return {
        "label": "phishing",
        "category": "university_portal_warning",
        "subject": random.choice(subjects),
        "body": join_lines(lines)
    }

# =============================================
# BIULDER COLLECTIONS
# =============================================

LEGIT_BIULDERS = [
    make_legit_shipping,
    make_legit_meeting,
    make_legit_invoice,
    make_legit_newsletter,
    make_legit_support_reply,
    make_legit_password_reset_confirmation,
]

PHISH_BIULDERS = [
    make_phish_account_verification,
    make_phish_delivery_problem,
    make_phish_password_expery,
    make_phish_document_share,
    make_phish_payment_issue,
    make_phish_university_portal,
]

# ======================================
# MASTER GENERATOR
# ======================================

def generate_email(force_label: str = None) -> Dict [str, str]:
    style = random.choice(STYLE_OPTIONS)
    length = random.choice(LENGTH_OPTIONS)

    if force_label == "legitimate":
        biulder = random.choice(LEGIT_BIULDERS)
    elif force_label == "phishing":
        biulder = random.choice(PHISH_BIULDERS)
    else:
        biulder = random.choice(PHISH_BIULDERS if random.random()< 0.5 else LEGIT_BIULDERS)

    email = biulder(style, length)
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