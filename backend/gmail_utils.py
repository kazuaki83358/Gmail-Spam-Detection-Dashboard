import imaplib
import email
import re
import string
import joblib
from email.header import decode_header

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# ---------- LOAD MODEL ----------
model = joblib.load("./model/spam_model.joblib")
vectorizer = joblib.load("./model/vectorizer.joblib")

# ---------- CLEANING ----------
def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    t = text.lower()
    t = re.sub(r"http\S+|www\S+", " ", t)
    t = re.sub(r"\S+@\S+", " ", t)
    t = re.sub(r"<.*?>", " ", t)
    t = re.sub(r"\d+", " ", t)
    t = t.translate(str.maketrans("", "", string.punctuation))
    t = re.sub(r"\s+", " ", t).strip()
    
    words = [lemmatizer.lemmatize(w) for w in t.split() if w not in stop_words]
    return " ".join(words)

# ---------- SAFE EMAIL BODY EXTRACTION ----------
def get_body(msg):
    """
    Safely extract email body from any message type.
    Handles:
    - multipart emails
    - html-only emails
    - plain text emails
    - empty payload emails
    """
    try:
        if msg.is_multipart():

            # Try text/plain first
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        return payload.decode(errors="ignore")

            # Try HTML next
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html = payload.decode(errors="ignore")
                        text = re.sub(r"<[^>]+>", " ", html)
                        return text

        else:
            # Single-part email
            payload = msg.get_payload(decode=True)
            if payload:
                return payload.decode(errors="ignore")

        return ""  # fallback body

    except Exception:
        return ""

def decode_mime(s):
    parts = decode_header(s)
    decoded = ""
    for p, enc in parts:
        if isinstance(p, bytes):
            decoded += p.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += p
    return decoded

#  MAIN SCAN FUNCTION 
def scan_gmail(email_user, app_password, limit=20):
    M = imaplib.IMAP4_SSL("imap.gmail.com")
    M.login(email_user, app_password)
    M.select("INBOX")

    _, data = M.search(None, "ALL")
    email_ids = data[0].split()[-limit:]

    results = []

    for eid in email_ids:
        _, msg_data = M.fetch(eid, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        subject = decode_mime(msg.get("Subject", ""))
        sender = decode_mime(msg.get("From", ""))
        date = msg.get("Date", "")

        raw_body = get_body(msg)
        body = clean_text(raw_body)

        vec = vectorizer.transform([body])
        pred = model.predict(vec)[0]

        results.append({
            "id": eid.decode(),
            "subject": subject,
            "from": sender,
            "date": date,
            "clean_text": body[:200],
            "prediction": int(pred),
            "label": "SPAM" if pred == 1 else "HAM"
        })

    M.logout()
    return results
