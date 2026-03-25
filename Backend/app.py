"""
Local Flask API for PhishDefender inbox loading and email classification.
"""

from pathlib import Path
import imaplib
import joblib
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from email_service import fetch_all_emails

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "Frontend"
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

app = Flask (
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)
CORS(app)

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def serve_frontend_file(filename):
    return send_from_directory(FRONTEND_DIR, filename)

MODEL = joblib.load(MODELS_DIR / "phishing_model.pkl")
VECTORIZER = joblib.load(MODELS_DIR / "vectorizer.pkl")

# ==================================================
# Load trusted domains
# ==================================================

trusted_domains = set()
domains_path = DATA_DIR / "domains.csv"

try:
    domains_df = pd.read_csv(domains_path)

    print("Trusted domains columns:", domains_df.columns.tolist())

    if "Domain" in domains_df.columns:
        trusted_domains = set(
            domains_df["Domain"].dropna().astype(str).str.strip().str.lower()
        )
    elif "domain" in domains_df.columns:
        trusted_domains = set(
            domains_df["domain"].dropna().astype(str).str.strip().str.lower()
        )
    else:
        print("No 'Domain' or 'domain' column found in domains.csv")

    print(f"Loaded {len(trusted_domains)} trusted domains")

except Exception as e:
    print("Could not load trusted domains:", e)


# ==================================================
# Helper functions
# ==================================================

def extract_sender_domain(sender: str) -> str:
    """
    Extract domain from strings like:
    Google <no-reply@accounts.google.com>
    no-reply@gmail.com
    """
    sender = (sender or "").strip().lower()

    if "<" in sender and ">" in sender:
        start = sender.find("<") + 1
        end = sender.find(">")
        sender = sender[start:end].strip()

    if "@" in sender:
        return sender.split("@")[-1].strip()

    return ""


def reduce_to_base_domain(domain: str) -> str:
    """
    Converts subdomains to a simpler base domain.
    Example:
    accounts.google.com -> google.com
    mail.github.com -> github.com
    """
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


# ==================================================
# Classification
# ==================================================

def classify_email(email_item: dict) -> dict:
    subject = (email_item.get("subject") or "").strip()
    sender = (email_item.get("from") or "").strip()
    body = (email_item.get("body") or "").strip()

    combined_text = f"""Subject: {subject}
From: {sender}
Body: {body}""".strip()

    text_vector = VECTORIZER.transform([combined_text])
    prediction = MODEL.predict(text_vector)[0]

    confidence = None
    if hasattr(MODEL, "predict_proba"):
        probs = MODEL.predict_proba(text_vector)[0]
        class_index = list(MODEL.classes_).index("phishing")
        confidence = float(probs[class_index])
    elif hasattr(MODEL, "decision_function"):
        raw_score = float(MODEL.decision_function(text_vector)[0])
        confidence = max(0.0, min(1.0, (raw_score + 3.0) / 6.0))

    # Extract sender domain
    sender_domain = extract_sender_domain(sender)
    base_domain = reduce_to_base_domain(sender_domain)

    is_trusted = (
        sender_domain in trusted_domains or
        base_domain in trusted_domains
    )

    # Override phishing if trusted and not extremely high confidence
    if is_trusted and prediction == "phishing":
        if confidence is None or confidence < 0.90:
            prediction = "legitimate"

    print("\n--- Email Classification ---")
    print("Subject:", subject)
    print("From:", sender)
    print("Sender domain:", sender_domain)
    print("Base domain:", base_domain)
    print("Trusted sender:", is_trusted)
    print("Prediction:", prediction)
    print("Confidence:", confidence)
    print("----------------------------")

    enriched = dict(email_item)
    enriched["prediction"] = prediction
    enriched["phishing_confidence"] = confidence
    enriched["sender_domain"] = sender_domain
    enriched["trusted_sender"] = is_trusted
    return enriched


# ==================================================
# Routes
# ==================================================

@app.route("/api/emails", methods=["POST"])
def emails():
    """
    Expects JSON:
    {
        "email": "email@gmail.com",
        "appPassword": "16 character app password"
    }
    """
    data = request.get_json(force=True)

    gmail_address = (data.get("email") or "").strip()
    app_password = (data.get("appPassword") or "").strip()

    if not gmail_address or not app_password:
        return jsonify({"error": "Missing email or appPassword"}), 400

    try:
        emails = fetch_all_emails(gmail_address, app_password)
        classified = [classify_email(item) for item in emails]

        phishing = [item for item in classified if item.get("prediction") == "phishing"]
        legitimate = [item for item in classified if item.get("prediction") == "legitimate"]

        return jsonify({
            "count": len(classified),
            "emails": classified,
            "phishing": phishing,
            "legitimate": legitimate,
        })

    except imaplib.IMAP4.error as exc:
        return jsonify({"error": f"IMAP error: {str(exc)}"}), 401
    except Exception as exc:
        return jsonify({"error": f"Server error: {str(exc)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)