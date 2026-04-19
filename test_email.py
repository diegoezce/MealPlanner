"""
Quick email test - sends a test email using Gmail SMTP.
Usage: python3 test_email.py [recipient@email.com]
"""
import os
import sys
import smtplib
import subprocess
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

FROM_EMAIL = "diegoezce@gmail.com"
TO_EMAIL = sys.argv[1] if len(sys.argv) > 1 else FROM_EMAIL

TEST_HTML = """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:#2c6e49;color:white;padding:20px;border-radius:8px;text-align:center;">
    <h2>🍽️ Test Email - Meal Planner</h2>
  </div>
  <p style="margin-top:20px;">Si recibís este email, el envío por <strong>Gmail SMTP</strong> está funcionando correctamente.</p>
  <p style="color:#888;font-size:12px;">Test enviado desde test_email.py</p>
</body></html>
"""

app_password = os.environ.get("GMAIL_APP_PASSWORD")
if not app_password:
    try:
        result = subprocess.run(
            ["bash", "-c", "source ~/.zshrc && echo $GMAIL_APP_PASSWORD"],
            capture_output=True, text=True, timeout=5
        )
        app_password = result.stdout.strip()
    except Exception:
        pass

if not app_password:
    print("❌ GMAIL_APP_PASSWORD no encontrado en env ni en ~/.zshrc")
    sys.exit(1)

try:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "✅ Test Meal Planner - Gmail SMTP"
    msg["To"] = TO_EMAIL
    msg["From"] = FROM_EMAIL
    msg.attach(MIMEText(TEST_HTML, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(FROM_EMAIL, app_password)
        server.sendmail(FROM_EMAIL, TO_EMAIL, msg.as_string())

    print(f"✅ Email enviado a {TO_EMAIL}")
    print(f"   From: {FROM_EMAIL}")
except Exception as e:
    print(f"❌ Error: {e}")
