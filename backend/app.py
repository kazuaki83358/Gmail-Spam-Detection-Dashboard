# backend/app.py
from flask import Flask, request, jsonify
from gmail_utils import scan_gmail
import imaplib

app = Flask(__name__)

# ------------------ SCAN EMAILS ------------------
@app.route("/scan", methods=["POST"])
def scan():
    data = request.json
    email_user = data.get("email")
    app_password = data.get("app_password")
    limit = data.get("limit", 20)

    if not email_user or not app_password:
        return jsonify({"error": "Missing credentials"}), 400

    try:
        results = scan_gmail(email_user, app_password, limit)
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ DELETE EMAIL ------------------
@app.route("/delete", methods=["POST"])
def delete_email():
    data = request.json
    email_user = data.get("email")
    app_password = data.get("app_password")
    mail_id = data.get("mail_id")

    if not email_user or not app_password or not mail_id:
        return jsonify({"error": "Missing parameters"}), 400

    try:
        # Connect to Gmail via IMAP
        M = imaplib.IMAP4_SSL("imap.gmail.com")
        M.login(email_user, app_password)
        M.select("INBOX")

        # Mark email as deleted
        M.store(mail_id, "+FLAGS", "\\Deleted")

        # Permanently delete
        M.expunge()
        M.logout()

        return jsonify({"success": True, "deleted_id": mail_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ RUN SERVER ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
