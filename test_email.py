"""
Quick email test - sends a test email using Gmail API.
Usage: python3 test_email.py [recipient@email.com]
"""
import os
import sys
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDS_FILE = os.path.expanduser("~/.claude/credentials/mealplanner-gcp.json")
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

TO_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "diegoezce@gmail.com"

TEST_HTML = """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:#2c6e49;color:white;padding:20px;border-radius:8px;text-align:center;">
    <h2>🍽️ Test Email - Meal Planner</h2>
  </div>
  <p style="margin-top:20px;">Si recibís este email, el envío por <strong>Gmail API</strong> está funcionando correctamente.</p>
  <p style="color:#888;font-size:12px;">Test enviado desde generate_and_send_meals.py</p>
</body></html>
"""

try:
    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gmail = build("gmail", "v1", credentials=creds)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "✅ Test Meal Planner - Gmail API"
    msg["To"] = TO_EMAIL
    msg["From"] = creds.service_account_email
    msg.attach(MIMEText(TEST_HTML, "html"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = gmail.users().messages().send(userId="me", body={"raw": raw}).execute()

    print(f"✅ Email enviado a {TO_EMAIL}")
    print(f"   Message ID: {result.get('id')}")
    print(f"   From: {creds.service_account_email}")
except FileNotFoundError:
    print(f"❌ Credenciales no encontradas: {CREDS_FILE}")
except Exception as e:
    print(f"❌ Error: {e}")
