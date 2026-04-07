"""
Local Flask API for PhishDefender inbox loading and email classification.
"""
import imaplib
import joblib
import pandas as pd
import numpy as np
import re

from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lime.lime_text import LimeTextExplainer
from email_service import fetch_all_emails
from scipy.sparse import hstack, csr_matrix

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

CLASS_NAMES = list(MODEL.classes_)

LIME_EXPLAINER = LimeTextExplainer(
    class_names=CLASS_NAMES
)

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

def normalise_email_text(text: str) -> str:
    text = str(text or "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)\bsubject:\b", " ", text)
    text = re.sub(r"(?i)\bfrom:\b", " ", text)
    text = re.sub(r"(?i)\bbody:\b", " ", text)
    return text.strip().lower()

def count_links(text: str) -> str:
    text = str(text or "")
    return len(re.findall(r"https[s]?://|www\.", text, flags=re.IGNORECASE))

def contains_urgent_words(text: str) -> int:
    text = str(text or "").lower()
    urgent_words = [
        "urgent", "immediately", "suspended", "verify now",
        "action required", "limited time", "warning", "alert"
    ]
    return int(any(word in text for word in urgent_words))

def contains_account_words(text: str) -> int:
    text = str(text or "").lower()
    account_words = [
        "account", "login", "sign in", "password", "username",
        "verify", "authentication", "secuirty"
    ]
    return int(any(word in text for word in account_words))

def contains_payment_words(text: str) -> int:
    payment_words = [
        "payment", "invoice", "bank", "card", "refund",
        "billing", "transaction", "transfer"
    ]
    return int(any(word in text for word in payment_words))

def exclamation_count(text: str) -> int:
    return str(text or "").count("!")

def uppercase_ratio(text: str) -> float:
    text = str(text or "")
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters)

def build_engineered_features_from_texts(texts):
    features = pd.DataFrame({
        "link_count": [count_links(text) for text in texts],
        "has_urgent_words": [contains_urgent_words(text) for text in texts],
        "has_account_words": [contains_account_words(text) for text in texts],
        "has_payment_words": [contains_payment_words(text) for text in texts],
        "exclamation_count": [exclamation_count(text) for text in texts],
        "uppercase_ratio": [uppercase_ratio(text) for text in texts]
    })
    return csr_matrix(features.values)

def build_model_input(texts):
    cleaned_texts = [normalise_email_text(text) for text in texts]
    text_vectors = VECTORIZER.transform(cleaned_texts)
    extra_vectors = build_engineered_features_from_texts(cleaned_texts)
    return hstack([text_vectors, extra_vectors])

def predict_proba_for_lime(texts):
    model_input = build_model_input(texts)

    if hasattr(MODEL, "predict_proba"):
        return MODEL.predict_proba(model_input)
    
    if hasattr(MODEL, "decision_function"):
        scores = MODEL.decision_function(model_input)

        if len(scores.shape) == 1:
            probs_pos = 1 / (1 + np.exp(-scores))
            probs_neg = 1 - probs_pos
            return np.vstack([probs_neg, probs_pos]).T
        
    predictions = MODEL.predict(model_input)
    output = []

    for pred in predictions:
        if pred == "phishing":
            output.append([0.0, 1.0])
        else:
            output.append([1.0, 0.0])

    return np.array(output)

def generate_lime_explanation(combined_text, predicted_label):
    try:
        explanation = LIME_EXPLAINER.explain_instance(
            combined_text,
            predict_proba_for_lime,
            num_features=6
        )

        label_index = CLASS_NAMES.index(predicted_label)
        feature_weights = explanation.as_list(label=label_index)

        top_features = []
        for feature, weight in feature_weights:
            top_features.append({
                "feature": feature,
                "weight": round(float(weight), 4)
            })
        positive_features = [
            item["feature"]
            for item in top_features
            if item["weight"] > 0
        ]

        if predicted_label == "phishing":
            if positive_features:
                summary = (
                    "This email was flagged as phishing because the model found suspicious language such as: "#
                    + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = (
                    "This email was flagged as phishing because the model found language patterns associated with phishing emails."
                )

        else:
            if positive_features:
                sumary = (
                    "This email was marked as legitimate becuase the model found more normal-looking language such as: "
                    + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = (
                    "This email was marked as legitimate because the model found language patterns more consistent with safe emails."
                )
        
        return {
            "summary": summary,
            "features": top_features
        }
    
    except Exception as e:
        print("LIME ERROR:", str(e))
        return {
            "summary": "Explanation could not be generated for this email.",
            "features": [],
            "error": str(e)
        }
    

# ==================================================
# Classification
# ==================================================

def classify_email(email_item: dict) -> dict:
    subject = (email_item.get("subject") or "").strip()
    sender = (email_item.get("from") or "").strip()
    body = (email_item.get("body") or "").strip()

    combined_text = f"""{sender} {subject} {body}""".strip()
    cleaned_text = normalise_email_text(combined_text)

    model_input = build_model_input([cleaned_text])
    prediction = MODEL.predict(model_input)[0]

    phishing_confidence = None
    legitimate_confidence = None

    if hasattr(MODEL, "predict_proba"):
        probs = MODEL.predict_proba(model_input)[0]
        classes = list(MODEL.classes_)

        phishing_index = classes.index("phishing")
        legitimate_index = classes.index("legitimate")

        phishing_confidence = float(probs[phishing_index])
        legitimate_confidence = float(probs[legitimate_index])

    elif hasattr(MODEL, "decision_function"):
        raw_score = float(MODEL.decision_function(model_input)[0])
        phishing_confidence = max(0.0, min(1.0, (raw_score + 3.0) / 6.0))
        legitimate_confidence = 1.0 - phishing_confidence

    lime_data = generate_lime_explanation(combined_text, prediction)

    # Extract sender domain
    sender_domain = extract_sender_domain(sender)
    base_domain = reduce_to_base_domain(sender_domain)

    is_trusted = (
        sender_domain in trusted_domains or
        base_domain in trusted_domains
    )

    engineered_details = {
        "link_count": count_links(cleaned_text),
        "has_urgent_words": bool(contains_urgent_words(cleaned_text)),
        "has_account_words": bool(contains_account_words(cleaned_text)),
        "has_payment_words": bool(contains_payment_words(cleaned_text)),
        "exclamation_count": exclamation_count(cleaned_text),
        "uppercase_ratio": round(uppercase_ratio(cleaned_text), 4)
    }

    explanation_summary = []

    if prediction == "phishing":

        if not is_trusted:
            explanation_summary.append("Sender domain is not trusted")
        
        if engineered_details["link_count"] > 0:
            explanation_summary.append("Email contains links")

        if engineered_details["has_urgent_words"]:
            explanation_summary.append("Uses urgent or theratening language")
        
        if engineered_details["has_account_words"]:
            explanation_summary.append("request account or login information")
        
        if engineered_details["has_payment_words"]:
            explanation_summary.append("Mentions payments or financial information")
        
        if engineered_details["uppercase_ratio"]:
            explanation_summary.append("Excessive use of exclamation marks")

        if not explanation_summary:
            explanation_summary.append("Model derected suspicous patterns")
    
    else:
        explanation_summary.append("Sender is from a trusted domain")

#    # Override phishing if trusted and not extremely high confidence
#    if is_trusted and prediction == "phishing":
#        if phishing_confidence is None or phishing_confidence < 0.90:
#            prediction = "legitimate"
# During live inbox testing, i observed that because i was generating emails with either phishing or 
# legitimate emails from phishdefender.sender@gmail.com it was just trusting that email address so 
# this block was removed 

    print("\n--- Email Classification ---")
    print("Subject:", subject)
    print("From:", sender)
    print("Sender domain:", sender_domain)
    print("Base domain:", base_domain)
    print("Trusted sender:", is_trusted)
    print("Prediction:", prediction)
    print("Phishing Confidence:", phishing_confidence)
    print("Legitimate Confidence:", legitimate_confidence)
    print()
    print("----------------------------")

    enriched = dict(email_item)
    enriched["prediction"] = prediction
    enriched["phishing_confidence"] = phishing_confidence
    enriched["legitimate_confidence"] = legitimate_confidence
    enriched["sender_domain"] = sender_domain
    enriched["trusted_sender"] = is_trusted
    enriched["explanation_summary"] = explanation_summary
    enriched["explanation_features"] = lime_data["features"]
    
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