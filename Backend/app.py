"""
Local Flask API to expose inbox emails to the frontend
"""

from flask import Flask, request, jsonify
from email_service import fetch_recent_emails
import imaplib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/recent-emails", methods=["POST"])
def recent_emails():
    """
    Expects JSON:
    {
    "email": "email@gmail.com
    "appPassword: "16 cahracter app password",
    "limit": 50
    }
    """
    data = request.get_json(force=True)

    gmail_address = (data.get("email") or "").strip()
    app_password = (data.get("appPassword") or "").strip()
    limit = int(data.get("limit") or 50)

    if not gmail_address or not app_password:
        return jsonify({"error": "Missing email or appPassword" }), 400
    
    # saftey cap
    limit =max(1, min(limit, 200))

    try: 
        emails = fetch_recent_emails(gmail_address, app_password, limit=limit)
        return jsonify({"count": len(emails), "emails": emails})
    
    except imaplib.IMAP4.error as e:
        return jsonify({"error": f"IMAP error: {str(e)}"}), 401
    
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)