"""
Quick email test - sends a test email via Mailjet from info@goplanify.com.
Usage: python3 test_email.py [recipient@email.com]
"""
import sys
import requests

MAILJET_API_KEY = "4dcbef529810c682b8d17535a8e3e651"
MAILJET_API_SECRET = "a74f1469aeb2b4c8bc29c468385fbc31"
TO_EMAIL = sys.argv[1] if len(sys.argv) > 1 else "diegoezce@gmail.com"

TEST_HTML = """
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:#2c6e49;color:white;padding:20px;border-radius:8px;text-align:center;">
    <h2>🍽️ Test Email - Meal Planner</h2>
  </div>
  <p style="margin-top:20px;">Si recibís este email, el envío por <strong>Mailjet / Goplanify</strong> está funcionando correctamente.</p>
  <p style="color:#888;font-size:12px;">From: info@goplanify.com via Mailjet</p>
</body></html>
"""

data = {
    "Messages": [
        {
            "From": {"Email": "info@goplanify.com", "Name": "Goplanify"},
            "To": [{"Email": TO_EMAIL}],
            "Subject": "✅ Test Meal Planner - Goplanify",
            "TextPart": "",
            "HTMLPart": TEST_HTML,
            "Headers": {"X-Transport": "mailjet_api"},
        }
    ]
}

try:
    response = requests.post(
        "https://api.mailjet.com/v3.1/send",
        json=data,
        auth=(MAILJET_API_KEY, MAILJET_API_SECRET),
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()
    msg_status = result.get("Messages", [{}])[0]
    if msg_status.get("Status") == "success":
        print(f"✅ Email enviado a {TO_EMAIL}")
        print(f"   From: info@goplanify.com")
        print(f"   Message ID: {msg_status.get('To', [{}])[0].get('MessageID', 'N/A')}")
    else:
        print(f"❌ Mailjet error: {msg_status.get('Errors', [])}")
except Exception as e:
    print(f"❌ Error: {e}")
