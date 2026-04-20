"""
Orchestrator: Read Google Sheet, generate meal plans via Claude, send emails.
No external API key needed - Claude generates the plans.

Usage: python3 orchestrate.py
"""
import os
import json
import requests
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDS_FILE = os.path.expanduser("~/.claude/credentials/mealplanner-gcp.json")
SPREADSHEET_ID = "1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM"

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

SHOPPING_NAMES = {
    "produce": "Verduras y Frutas",
    "proteins": "Proteínas",
    "dairy": "Lácteos",
    "pantry": "Despensa",
    "frozen": "Congelados",
    "other": "Otros",
}


def build_html_email(plan: dict) -> str:
    """Build HTML email from meal plan."""
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
  Plan generado el {plan['generated_date']} · Submission ID: {plan['submission_id']}
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


def col_to_letter(idx: int) -> str:
    """Convert 0-based column index to letter (A, B, ..., Z, AA, ...)."""
    result = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        result = chr(65 + rem) + result
    return result


def update_sheet_cell(sheets, row_idx: int, col_letter: str, value: str):
    """Update a single cell in the sheet."""
    cell = f"{col_letter}{row_idx}"
    sheets.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=cell,
        valueInputOption="RAW",
        body={"values": [[value]]},
    ).execute()


def main():
    # Authenticate
    creds = service_account.Credentials.from_service_account_file(
        CREDS_FILE, scopes=SCOPES
    )
    sheets = build("sheets", "v4", credentials=creds)

    # Read sheet
    result = sheets.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range="A1:Z"
    ).execute()
    rows = result.get("values", [])

    if not rows:
        print("❌ Sheet is empty.")
        return

    headers = rows[0]

    # Find columns
    col_map = {}
    for i, h in enumerate(headers):
        h_lower = h.strip().lower()
        if h_lower == "status":
            col_map["status"] = i
        elif h_lower == "submission id":
            col_map["submission_id"] = i
        elif "family size" in h_lower or "personas" in h_lower:
            col_map["family_size"] = i
        elif "age" in h_lower or "edad" in h_lower:
            col_map["ages"] = i
        elif "restriction" in h_lower or "restriccion" in h_lower:
            col_map["restrictions"] = i
        elif "picky" in h_lower or "come poco" in h_lower:
            col_map["picky_eaters"] = i
        elif "cooking" in h_lower or "tiempo" in h_lower:
            col_map["cooking_time"] = i
        elif "preference" in h_lower or "prefieren" in h_lower:
            col_map["preferences"] = i
        elif "email" in h_lower or "contact" in h_lower or "envio" in h_lower:
            col_map["email"] = i
        elif "last recipe" in h_lower or "ultimas recetas" in h_lower:
            col_map["last_recipes"] = i

    # Add status column if missing
    if "status" not in col_map:
        col_map["status"] = len(headers)
        status_col_letter = col_to_letter(col_map["status"])
        update_sheet_cell(sheets, 1, status_col_letter, "status")

    print(f"📋 Found {len(rows) - 1} rows to process")
    print(f"📍 Columns: {col_map}\n")

    processed = 0
    errors = 0

    # Process each row
    for row_idx, row in enumerate(rows[1:], start=2):
        status_col = col_map.get("status", 0)
        current_status = row[status_col] if len(row) > status_col else ""

        if current_status not in ("", None):
            print(f"⏭️  Row {row_idx} already processed: {current_status}")
            continue

        # Extract data
        submission_id = row[col_map.get("submission_id", 0)] if col_map.get("submission_id") is not None else f"row_{row_idx}"
        to_email = row[col_map.get("email", -1)].strip() if col_map.get("email") is not None and len(row) > col_map.get("email", -1) else ""

        if not to_email:
            print(f"❌ Row {row_idx}: No email found")
            update_sheet_cell(sheets, row_idx, col_to_letter(status_col), "Error: no email")
            errors += 1
            continue

        row_data = {
            "family_size": row[col_map.get("family_size", -1)].strip() if col_map.get("family_size") is not None and len(row) > col_map.get("family_size", -1) else "",
            "ages": row[col_map.get("ages", -1)].strip() if col_map.get("ages") is not None and len(row) > col_map.get("ages", -1) else "",
            "restrictions": row[col_map.get("restrictions", -1)].strip() if col_map.get("restrictions") is not None and len(row) > col_map.get("restrictions", -1) else "",
            "picky_eaters": row[col_map.get("picky_eaters", -1)].strip() if col_map.get("picky_eaters") is not None and len(row) > col_map.get("picky_eaters", -1) else "",
            "cooking_time": row[col_map.get("cooking_time", -1)].strip() if col_map.get("cooking_time") is not None and len(row) > col_map.get("cooking_time", -1) else "",
            "preferences": row[col_map.get("preferences", -1)].strip() if col_map.get("preferences") is not None and len(row) > col_map.get("preferences", -1) else "",
        }

        last_recipes = row[col_map.get("last_recipes", -1)] if col_map.get("last_recipes") is not None and len(row) > col_map.get("last_recipes", -1) else ""

        print(f"🔄 Row {row_idx}: {to_email}")
        print(f"   Family: {row_data['family_size']} ({row_data['ages']})")
        print(f"   Picky eaters: {row_data['picky_eaters']}")
        print(f"   Waiting for Claude to generate plan...")
        print()

        try:
            # Create prompt for Claude to generate plan
            prompt = f"""Generate a personalized 7-day LatAm meal plan for this family:
- Family size: {row_data['family_size']} people
- Ages: {row_data['ages']}
- Restrictions: {row_data['restrictions']}
- Picky eaters: {row_data['picky_eaters']}
- Cooking time: {row_data['cooking_time']}
- Preferences: {row_data['preferences']}

Previous recipes (avoid repeating):
{last_recipes if last_recipes else "None - first week"}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "meal_plan": {{
    "monday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "tuesday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "wednesday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "thursday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "friday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "saturday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}},
    "sunday": {{"breakfast": "...", "lunch": "...", "dinner": "..."}}
  }},
  "shopping_list": {{
    "produce": ["item1", "item2"],
    "proteins": ["item1"],
    "dairy": ["item1"],
    "pantry": ["item1"],
    "frozen": [],
    "other": []
  }},
  "meal_prep_tips": ["tip1", "tip2", "tip3"],
  "key_insights": {{
    "avg_prep_time_mins": 20,
    "picky_friendly_meals": 18,
    "ingredient_reuse_count": 8,
    "healthier_options": 3,
    "budget_notes": "Plan is budget-friendly with..."
  }}
}}"""

            print(f"📋 PROMPT FOR CLAUDE:\n{prompt}\n")
            print("=" * 80)
            print("❌ MANUAL STEP REQUIRED")
            print("=" * 80)
            print(f"\n1. Copy the prompt above ☝️")
            print(f"2. Paste it in a new Claude chat")
            print(f"3. Get the JSON response")
            print(f"4. Save response to: plan_comidas_{submission_id}.json")
            print(f"5. Run: python3 send_meal_plan.py")
            print()

            update_sheet_cell(sheets, row_idx, col_to_letter(status_col), "Waiting for Claude generation")

        except Exception as e:
            print(f"❌ Row {row_idx}: {str(e)}")
            update_sheet_cell(sheets, row_idx, col_to_letter(status_col), f"Error: {str(e)[:50]}")
            errors += 1

    print(f"\n⚠️  All rows require manual Claude generation")
    print(f"   (To avoid API key costs, generate plans manually)")


if __name__ == "__main__":
    main()
