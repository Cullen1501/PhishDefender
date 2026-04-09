"""
Local Flask API for PhishDefender inbox loading and email classification.

what this file does
1. Serves the frontend files
2. Loads the trained ML model and vectorizer
3. Loads trusted domains from a CSV
4. Builds extra phishing related  feaures for each email
5. Classifies emails as phishing or legitimate
6. Generates explanations using:
    - Custom rule based logic
    - LIME
    - SHAP
7. Returns all results to the frtonend as JSON
"""

# Imports

import imaplib          # Handels Gmail IMAP logic errors
import joblib           # Loads saved ML model and vectorizer
import pandas as pd     # Used for feature tables and CSV loading 
import numpy as np      # Used for probability calculations and arrays
import re               # Used for text cleaning and regex checks
import shap             # Used for SHAp explainability

from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from lime.lime_text import LimeTextExplainer
from email_service import fetch_all_emails
from scipy.sparse import hstack, csr_matrix

# Paths and App Setup

# Base project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Frontend folder for HTML/CSS/JS
FRONTEND_DIR = BASE_DIR / "Frontend"

# Folder containing trained model files
MODELS_DIR = BASE_DIR / "models"

# Folder contaning datasets / trusted domain CSV
DATA_DIR = BASE_DIR / "data"

# Create Flask app
app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR),
    static_url_path=""
)

# Allow frontend JS to call backend API
CORS(app)

# Frontend Routes

# Serves the homepage
@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")

# Serves an other frontend file such as CSS, JS, images, other HTML pages
@app.route("/<path:filename>")
def serve_frontend_file(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# Load Model and Vectroizer

# Load the best trained model
MODEL = joblib.load(MODELS_DIR / "phishing_model.pkl")

# Locate the TF-IDF vectorizer used during training
VECTORIZER = joblib.load(MODELS_DIR / "vectorizer.pkl")

# Store class names exactly as used by the model
CLASS_NAMES = list(MODEL.classes_)

# Names of the extra engineered features added beside TF-IDF
ENGINEERED_FEATURE_NAMES = [
    "link_count",
    "has_urgent_words",
    "has_account_words",
    "has_payment_words",
    "exclamation_count",
    "uppercase_ratio",
]

# Create LIME explainer once when the app starts
LIME_EXPLAINER = LimeTextExplainer(
    class_names=CLASS_NAMES
)

# SHAP explainer is created lazily later
SHAP_EXPLAINER = None
SHAP_INIT_ATTEMPTED = False


# Load Trusted Domains

# This set stores trusted domains such as google.com, microsoft.com etc.
trusted_domains = set()

# File path for tursted domains CSV
domains_path = DATA_DIR / "domains.csv"

try:
    domains_df = pd.read_csv(domains_path)

    print("Trusted domains columns:", domains_df.columns.tolist())

    # Support either "Domain" or "domain" column name
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

except Exception as e:
    print("Could not load trusted domains: ", e)

# Helper Functions - Sender Domain

def extract_sender_domain(sender: str) -> str:
    """
    Extracts email domain from sender strings like:
    Google <no-reply@accounts.google.com>
    no-reply@gmail.com

    Returns just the domain part.
    """
    sender = (sender or "").strip().lower()

    # If sender is in format Name <email@domain.com>, pull out only email
    if "<" in sender and ">" in sender:
        start = sender.find("<") + 1
        end = sender.find(">")
        sender = sender[start:end].strip()
    
    # Return domain after @
    if "@" in sender:
        return sender.split("@")[-1].strip()
    
    return ""

def reduce_to_base_domain(domain: str) -> str:
    """
    Reduces subdomians to a base domain
    Example:
    accounts.google.com -> google.com
    mail.github.com -> github.com
    """
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain

# Helper Function - Text Cleaning

def normalise_email_text(text: str) -> str:
    """
    Cleans and standardises email text before vectorising. Removes repeated spaces and strips 
    structural words such as: Subject:, From:, Body:
    """
    text = str(text or "")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?i)\bsubject:\b", " ", text)
    text = re.sub(r"(?i)\bfrom:\b", " ", text)
    text = re.sub(r"(?i)\bbody:\b", " ", text)
    return text.strip().lower()

# Helper Functions - Engineered Featuers

def count_links(text: str) -> int:
    """
    Counts the number of visible links in the email text.
    """
    text = str(text or "")
    return len(re.findall(r"http[s]?://|www\.", text, flags=re.IGNORECASE))

def contains_urgent_words(text: str) -> int:
    """
    Returns 1 if urgent / threatening words appear, else 0
    """
    text = str(text or "").lower()
    urgent_words = [
        "urgent", "immediately", "suspended", "verify now",
        "action required", "limited time", "warning", "alert"
    ]
    return int(any(word in text for word in urgent_words))

def contains_account_words(text: str) -> int:
    """
    Returns 1 if account / login related words appear, else 0
    """
    text = str(text or "").lower()
    account_words = [
        "account", "login", "sign in", "password", "username",
        "verify", "authentication", "security"
    ]
    return int(any(word in text for word in account_words))

def contains_payment_words(text:str) -> int:
    """
    Return 1 if payment / banking related words appear, else 0
    """
    text = str(text or "").lower()
    payment_words = [
        "payment", "invoice", "bank", "card", "refund",
        "billing", "transaction", "transfer"
    ]
    return int(any(word in text for word in payment_words))

def exclamation_count(text: str) -> int:
    """
    Counts how many exclamation marks are in the text.
    """
    return str(text or "").count("!")

def uppercase_ratio(text: str) -> float:
    """
    Calculates what proportion of letters are uppercase. Useful for spotting unusally shouty emails.
    """
    text = str(text or "")
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())

    return upper / len(letters)

def build_engineered_features_from_texts(texts):
    """
    Builds the extra phishing realted feaures for one or more texts. Returns them as a sparse matrix
    so they can be stacked beside TF-IDF features
    """
    features = pd.DataFrame({
        "link_count": [count_links(text) for text in texts],
        "has_urgent_words": [contains_urgent_words(text) for text in texts],
        "has_account_words": [contains_account_words(text) for text in texts],
        "has_payment_words": [contains_payment_words(text) for text in texts],
        "exclamation_count": [exclamation_count(text) for text in texts],
        "uppercase_ratio": [uppercase_ratio(text) for text in texts],
    })
    return csr_matrix(features.values)

def build_model_input(texts):
    """
    Builds the final model Input: 
    TF-IDF text features + engineered phishing features
    """
    cleaned_texts = [normalise_email_text(text) for text in texts]
    text_vectors = VECTORIZER.transform(cleaned_texts)
    extra_vectors = build_engineered_features_from_texts(cleaned_texts)
    return hstack([text_vectors, extra_vectors])

# Helper Functions - SHAP

def get_all_feature_names():
    """
    Returns the full list of model feature names:
    TF-IDF feautres first, then engineered features.
    """
    tfidf_names = list(VECTORIZER.get_feature_names_out())
    return tfidf_names + ENGINEERED_FEATURE_NAMES

def get_shap_explainer():
    """
    Creates the SHAP explainer only once, when first needed.
    """
    global SHAP_EXPLAINER, SHAP_INIT_ATTEMPTED

    if SHAP_INIT_ATTEMPTED:
        return SHAP_EXPLAINER
    
    SHAP_INIT_ATTEMPTED = True

    try:
        # Create a simple empty background vector with same feature size
        background = csr_matrix((1, len(get_all_feature_names())))
        SHAP_EXPLAINER = shap.LinearExplainer(MODEL, background)
        print("SHAP explainer initialised.")
    except Exception as e:
        print("SHAP INIT ERROR:", str(e))
        SHAP_EXPLAINER = None

    return SHAP_EXPLAINER

def generate_shap_explanation(model_input, predicted_label, top_n=6):
    """
    Generates SHAP explanation for one email.
    Returns:
    - summary sentence
    - top contributing features 
    """
    explainer = get_shap_explainer()

    if explainer is None:
        return {
            "summary": "SHAP explanation is not available for this model.",
            "features": []
        }
    
    try:
        shap_values = explainer.shap_values(model_input)

        # Handle different SHAP output formats safely
        if isinstance(shap_values, list):
            label_index = CLASS_NAMES.index(predicted_label)
            values = np.asarray(shap_values[label_index]).ravel()
        else:
            values = np.asarray(shap_values)

            if values.ndim == 3:
                label_index = CLASS_NAMES.index(predicted_label)
                values = values[0, :, label_index]
            elif values.ndim == 2:
                values = values[0]
            else:
                values = values.ravel()
        
        feature_names = get_all_feature_names()

        pairs = []
        for feature, value in zip(feature_names, values):
            if abs (float(value)) < 1e-9:
                continue
            
            pairs.append({
                "feature": feature,
                "weight": round(float(value), 4)
            })
        
        # Keep strongest ffeatures only
        pairs = sorted(pairs, key=lambda x: abs(x["weight"]), reverse=True)[:top_n]

        positive_features = [item["feature"] for item in pairs if item["weight"] > 0]

        if predicted_label == "phishing":
            if positive_features:
                summary = (
                    "SHAP found the strongest phishing contribution from: "
                    + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = "SHAP did not find strong positive phishing driving features for this email."
        else:
            if positive_features:
                summary = (
                    "SHAP found the strongest safe email contribution from: "
                    + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = "SHAP did not find strong positive safe email driving features for this email."
        
        return {
            "summary": summary,
            "features": pairs
        }
    
    except Exception as e:
        print("SHAP ERROR:", str(e))
        return {
            "summary": "SHAP explanation could not be generated for this email.",
            "features": [],
            "error": str(e)
        }
    
# Helper Functions - Lime

def predict_proba_for_lime(texts):
    """
    LIME need a function that takes raw texts and returns class probabilities.
    This adapts the model into the format.
    """
    model_input = build_model_input(texts)

    if hasattr(MODEL, "predict_proba"):
        return MODEL.predict_proba(model_input)
        
    if hasattr(MODEL, "decision_function"):
        scores = MODEL.decision_function(model_input)

        # Convert single decision scores into two class probabilities
        if len(scores.shape) == 1:
            probs_pos = 1 / (1 + np.exp(-scores))
            probs_neg = 1 - probs_pos
            return np.vstack([probs_neg, probs_pos]).T
            
    # Fallback if predict_proba does not exsit
    predictions = MODEL.predict(model_input)
    output = []

    for pred in predictions:
        if pred == "phishing":
            output.append([0.0, 1.0])
        else:
            output.append([1.0, 0.0])
        
    return np.array(output)

def generate_lime_explanation(combined_text, predicted_label):
    """
    Generates LIME explanation for one email.
    Returns:
    - summary sentence
    - top contibuting text features
        """
    try: 
        safe_text = normalise_email_text(combined_text)

        # Skip extremely short texts
        if len(safe_text) < 20:
            return {
                "summary": "This email did not contain enough text for a detailed AI explanation.",
                "features": []
            }
            
        explanation = LIME_EXPLAINER.explain_instance(
            safe_text,
            predict_proba_for_lime,
            num_features=6
        )

        label_index = CLASS_NAMES.index(predicted_label)
        feature_weights = explanation.as_list(label=label_index)

        stop_tokens = {"subject", "from", "body", "com"}

        top_features = []
        for feature, weight in feature_weights:
            feature_clean = str(feature).strip()
            if feature_clean.lower() in stop_tokens:
                continue

            top_features.append({
                "feature": feature_clean,
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
                    "this email was flagged as phishing because the model found suspicous language such as: "
                    + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = (
                    "This email was flagged as phishing becuase the model found language patterns associated with phishing emails."
                )
        else:
            if positive_features:
                summary = (
                    "This email was marked as legitimate becuase the model found more normal looking language such as: "
                        + ", ".join(positive_features[:4]) + "."
                )
            else:
                summary = (
                    "This email was marked as legitimate becuase the model found language patterns more consistent with safe emails."
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

# Main Classification Function 

def classify_email(email_item: dict) -> dict:
    """
    Takes one email dictionary and returns:
    - classification
    - confidence scores
    - engineered features
    - trust checks
    - human explanation
    - LIME explanation
    - SHAP explanation
    """

    # Pull out main email fields
    subject = (email_item.get("subject") or "").strip()
    sender = (email_item.get("from") or "").strip()
    body = (email_item.get("body") or "").strip()

    # Extract sender domain and reduce to base domain
    sender_domain = extract_sender_domain(sender)
    base_domain = reduce_to_base_domain(sender_domain)

    # Build one combined text string
    combined_text = f"Subject: {subject}\nFrom: {sender}\nBody: {body}".strip()

    # Clean text properly as a STRING, not a list
    cleaned_text = normalise_email_text(combined_text)

    # Build model input using TF-IDF + engineered features
    # build_model_input expects a list of texts, so wrap once here only
    model_input = build_model_input([cleaned_text])

    # Predict phishing / legitimate
    prediction = MODEL.predict(model_input)[0]

    # Confidence scores
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

    # Generate explainability outputs
    lime_data = generate_lime_explanation(combined_text, prediction)
    shap_data = generate_shap_explanation(model_input, prediction)

    is_trusted = (
        sender_domain in trusted_domains or
        base_domain in trusted_domains
    )

    # Compute engineered details for frontend display
    engineered_details = {
        "link_count": count_links(cleaned_text),
        "has_urgent_words": bool(contains_urgent_words(cleaned_text)),
        "has_account_words": bool(contains_account_words(cleaned_text)),
        "has_payment_words": bool(contains_payment_words(cleaned_text)),
        "exclamation_count": exclamation_count(cleaned_text),
        "uppercase_ratio": round(uppercase_ratio(cleaned_text), 4)
    }

    # Human readable explanation
    explanation_summary = []

    if prediction == "phishing":
        if not is_trusted:
            explanation_summary.append("Sender domain is not trusted")

        if engineered_details["link_count"] > 0:
            explanation_summary.append("Email contains links")

        if engineered_details["has_urgent_words"]:
            explanation_summary.append("Uses urgent or threatening language")

        if engineered_details["has_account_words"]:
            explanation_summary.append("Requests account or login information")

        if engineered_details["has_payment_words"]:
            explanation_summary.append("Mentions payments or financial information")

        if engineered_details["exclamation_count"] > 3:
            explanation_summary.append("Excessive use of exclamation marks (!)")

        if engineered_details["uppercase_ratio"] > 0.30:
            explanation_summary.append("High use of uppercase text")

        if not explanation_summary:
            explanation_summary.append("Model detected suspicious patterns")

    else:
        explanation_summary.append("No strong phishing indicators detected")

        if is_trusted:
            explanation_summary.append("Sender is from a trusted domain")

        explanation_summary.append("Email appears safe based on language patterns")

    # Debug print in terminal
    print("\n--- Email Classification ---")
    print("Subject:", subject)
    print("From:", sender)
    print("Sender domain:", sender_domain)
    print("Base domain:", base_domain)
    print("Trusted sender:", is_trusted)
    print("Prediction:", prediction)
    print("Phishing confidence:", phishing_confidence)
    print("Legitimate confidence:", legitimate_confidence)
    print("Explanation Summary:", explanation_summary)
    print("LIME Summary:", lime_data.get("summary"))
    print("SHAP Summary:", shap_data.get("summary"))
    print("---------------------------------")

    # Build final response object
    enriched = dict(email_item)
    enriched["prediction"] = prediction
    enriched["phishing_confidence"] = phishing_confidence
    enriched["legitimate_confidence"] = legitimate_confidence
    enriched["sender_domain"] = sender_domain
    enriched["base_domain"] = base_domain
    enriched["trusted_sender"] = is_trusted
    enriched["engineered_features"] = engineered_details
    enriched["explanation_summary"] = explanation_summary
    enriched["lime_summary"] = lime_data.get("summary", "")
    enriched["lime_features"] = lime_data.get("features", [])
    enriched["shap_summary"] = shap_data.get("summary", "")
    enriched["shap_features"] = shap_data.get("features", [])
    
    #enriched["explanation_features"] = lime_data.get("features", [])  # compatibility with frontend 
    #(MIGHT BE ABLE TO REMOVE NOW!)

    return enriched

# API route - Fetch + Classify Emails

@app.route("/api/emails", methods=["POST"])
def emails():
    """
    Expects JSON like:
    {
        "email": "email@gmail.com",
        "appPassword": "16 character app password"
    }

    Steps:
    1. Login to Gmail
    2. Fetch inbox emails
    3. Classify each email
    4. Return all emails + phishing only + legitimate only 
    """
    data = request.get_json(force=True)

    gmail_address = (data.get("email") or "").strip()
    app_password = (data.get("appPassword") or "").strip()

    if not gmail_address or not app_password:
        return jsonify({"error": "Missing email or appPassword"}), 400
    
    try:
        emails = fetch_all_emails(gmail_address, app_password)
        classified = [classify_email(item) for item in emails]

        phishing = [email for email in classified if email["prediction"] == "phishing"]
        legitimate = [email for email in classified if email["prediction"] == "legitimate"]

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

@app.route("/api/emails/new", methods=["POST"])
def get_new_emails():
    data = request.get_json(force=True) or {}

    gmail_address = (data.get("email") or "").strip()
    app_password = (data.get("appPassword") or "").strip()
    last_seen_uid = data.get("lastSeenUid")

    if not gmail_address or not app_password:
        return jsonify({"error": "Missing email or app password."}), 400

    try:
        new_emails = fetch_all_emails(
            gmail_address,
            app_password,
            only_after_uid=int(last_seen_uid) if last_seen_uid is not None else None
        )

        results = [classify_email(email_obj) for email_obj in new_emails]

        return jsonify({
            "new_emails": results,
            "count": len(results)
        })

    except imaplib.IMAP4.error as exc:
        return jsonify({"error": f"IMAP error: {str(exc)}"}), 401

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
# Run App
if __name__ == "__main__":
    app.run(debug=True, port=5000)