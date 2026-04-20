"""
Send meal plan emails and mark Google Sheet rows as Done.
Usage: python3 scripts/send_meal_plan.py
"""
import os
import json
import requests

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDS_FILE = os.path.expanduser("~/.claude/credentials/mealplanner-gcp.json")
SPREADSHEET_ID = "1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM"
PLAN_FILE = "plan_comidas_1Wk5dxp.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

DAY_NAMES = {
    "monday": "Lunes",
    "tuesday": "Martes",
    "wednesday": "Miércoles",
    "thursday": "Jueves",
    "friday": "Viernes",
    "saturday": "Sábado",
    "sunday": "Domingo",
}

MEAL_NAMES = {
    "breakfast": "Desayuno",
    "lunch": "Almuerzo",
    "dinner": "Cena",
}

SHOPPING_NAMES = {
    "produce": "Verduras y Frutas",
    "proteins": "Proteínas",
    "dairy": "Lácteos",
    "pantry": "Despensa",
    "frozen": "Congelados",
    "other": "Otros",
}


def build_html_email(plan: dict) -> str:
    sub_id = plan["submission_id"]
    params = plan["parameters"]
    meal_plan = plan["meal_plan"]
    shopping = plan["shopping_list"]
    tips = plan["meal_prep_tips"]
    insights = plan["key_insights"]

    # Meal plan table rows
    table_rows = ""
    for day_key, meals in meal_plan.items():
        day_name = DAY_NAMES.get(day_key, day_key.capitalize())
        bf = meals.get("breakfast", "")
        ln = meals.get("lunch", "")
        dn = meals.get("dinner", "")
        table_rows += f"""
        <tr>
          <td style="font-weight:bold;background:#f9f4ee;">{day_name}</td>
          <td>{bf}</td>
          <td>{ln}</td>
          <td>{dn}</td>
        </tr>"""

    # Shopping list sections
    shopping_html = ""
    for section_key, items in shopping.items():
        section_name = SHOPPING_NAMES.get(section_key, section_key.capitalize())
        if items:
            items_html = "".join(f"<li>{item}</li>" for item in items)
            shopping_html += f"<h4 style='color:#555;margin:12px 0 4px;'>{section_name}</h4><ul style='margin:0 0 8px;'>{items_html}</ul>"

    # Tips
    tips_html = "".join(f"<li style='margin-bottom:8px;'>{tip}</li>" for tip in tips)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: Arial, sans-serif; color: #333; max-width: 700px; margin: 0 auto; padding: 20px; }}
    h2 {{ color: #2c6e49; }}
    h3 {{ color: #4a4a4a; border-bottom: 2px solid #e0e0e0; padding-bottom: 6px; margin-top: 30px; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
    th {{ background: #2c6e49; color: white; padding: 10px; text-align: left; }}
    td {{ padding: 9px 10px; border: 1px solid #ddd; vertical-align: top; font-size: 14px; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 4px; font-size: 14px; }}
    .insight-box {{ background: #f0f7f4; border-left: 4px solid #2c6e49; padding: 12px 16px; margin: 10px 0; border-radius: 4px; }}
    .footer {{ color: #888; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 12px; }}
  </style>
</head>
<body>

<h2>🍽️ Tu Plan de Comidas Personalizado</h2>
<p>¡Hola! Tu plan de comidas semanal está listo. Fue generado para una familia de <strong>{params['family_size']} personas</strong>
({params.get('ages', '')}) con tiempo de cocina de <strong>{params['cooking_time']}</strong>.</p>

<h3>📋 Plan de 7 Días</h3>
<table>
  <tr>
    <th>Día</th>
    <th>Desayuno</th>
    <th>Almuerzo / Vianda</th>
    <th>Cena</th>
  </tr>
  {table_rows}
</table>

<h3>🛒 Lista de Compras</h3>
{shopping_html}

<h3>💡 Tips de Meal Prep</h3>
<ul>
{tips_html}
</ul>

<h3>📊 Insights del Plan</h3>
<div class="insight-box">
  <ul style="margin:0;padding-left:18px;">
    <li>⏱️ Tiempo promedio de preparación: <strong>{insights['avg_prep_time_mins']} minutos</strong></li>
    <li>😊 Comidas picky-friendly: <strong>{insights['picky_friendly_meals']}/21</strong></li>
    <li>🔁 Ingredientes reutilizados: <strong>{insights['ingredient_reuse_count']}</strong></li>
    <li>🥗 Opciones saludables: <strong>{insights['healthier_options']}</strong></li>
    <li>💰 {insights['budget_notes']}</li>
  </ul>
</div>

<p>¡Espero que les sea útil! Si tenés preguntas o querés ajustar el plan, respondé este email.</p>
<p>¡Buen provecho! 🥘</p>

<div class="footer">
  Plan generado el {plan['generated_date']} · Submission ID: {sub_id}
</div>

</body>
</html>"""
    return html


def send_email_mailjet(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Mailjet using goplanify.com verified sender."""
    data = {
        "Messages": [
            {
                "From": {"Email": "info@goplanify.com", "Name": "Goplanify"},
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": "",
                "HTMLPart": html_body,
                "Headers": {"X-Transport": "mailjet_api"},
            }
        ]
    }
    try:
        r = requests.post(
            "https://api.mailjet.com/v3.1/send",
            auth=("86e75a4aec95416b39d15f8acb0b037c", "d420a490c00c0f983716e803b0e5272c"),
            json=data,
            timeout=15,
        )
        r.raise_for_status()
        msg_status = r.json().get("Messages", [{}])[0]
        if msg_status.get("Status") == "success":
            print(f"✅ Email sent to {to_email}")
            return True
        else:
            print(f"❌ Mailjet message error: {msg_status.get('Errors', [])}")
            return False
    except Exception as e:
        print(f"❌ Mailjet API failed: {e}")
        return False


def update_sheet_status(sheets, row_idx: int, status_col_letter: str, status: str):
    cell = f"{status_col_letter}{row_idx}"
    sheets.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=cell,
        valueInputOption="RAW",
        body={"values": [[status]]}
    ).execute()
    print(f"Sheet row {row_idx} marked: {status}")


def col_to_letter(idx: int) -> str:
    """Convert 0-based column index to letter (A, B, ..., Z, AA, ...)."""
    result = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def main():
    # Load plan
    with open(PLAN_FILE) as f:
        plan = json.load(f)

    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE, scopes=SCOPES
    )

    # Connect to Sheets
    sheets = build("sheets", "v4", credentials=creds)

    # Read sheet to find status column and target row
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="A1:Z"
    ).execute()
    rows = result.get("values", [])

    if not rows:
        print("Sheet is empty.")
        return

    headers = rows[0]
    status_col = None
    email_col = None
    submission_col = 0  # Submission ID is column A

    for i, h in enumerate(headers):
        h_lower = h.strip().lower()
        if h_lower == "status":
            status_col = i
        if "email" in h_lower or "whatsapp" in h_lower or "enviamos" in h_lower:
            email_col = i

    # Find email column by checking header content
    if email_col is None:
        for i, h in enumerate(headers):
            if "dónde" in h.lower() or "donde" in h.lower():
                email_col = i
                break

    print(f"Headers: {headers}")
    print(f"Status col: {status_col}, Email col: {email_col}")

    # Add status column if missing
    if status_col is None:
        status_col = len(headers)
        col_letter = col_to_letter(status_col)
        sheets.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{col_letter}1",
            valueInputOption="RAW",
            body={"values": [["status"]]}
        ).execute()
        print(f"Added 'status' column at {col_letter}")

    status_col_letter = col_to_letter(status_col)

    # Process unprocessed rows
    for row_idx, row in enumerate(rows[1:], start=2):
        current_status = row[status_col] if len(row) > status_col else ""
        if current_status in ("", None):
            submission_id = row[submission_col] if row else "unknown"

            # Match with plan file
            if submission_id != plan["submission_id"]:
                print(f"Row {row_idx} submission {submission_id} doesn't match plan {plan['submission_id']}, skipping")
                continue

            to_email = row[email_col].strip() if email_col is not None and len(row) > email_col else ""
            if not to_email:
                update_sheet_status(sheets, row_idx, status_col_letter, "Error: no email")
                continue

            print(f"Processing row {row_idx}: submission={submission_id}, to={to_email}")

            # Build HTML
            subject = f"🍽️ Tu plan de comidas semanal - {submission_id}"
            html_body = build_html_email(plan)

            # Send email
            success = send_email_mailjet(to_email, subject, html_body)

            status = "Done" if success else "Error: email send failed"
            update_sheet_status(sheets, row_idx, status_col_letter, status)
        else:
            print(f"Row {row_idx} already has status: {current_status}")

    print("Processing complete.")


if __name__ == "__main__":
    main()
