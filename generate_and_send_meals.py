"""
Weekly meal plan generator and sender.
Reads Google Sheet, generates plans with Claude API, sends emails via Mailjet.

Usage: python3 generate_and_send_meals.py
"""
import os
import json
import requests
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from anthropic import Anthropic

# Load credentials: try local file first, then environment variable (Railway)
_creds_file = os.path.expanduser("~/.claude/credentials/mealplanner-gcp.json")
CREDS_FILE = _creds_file

if not os.path.exists(_creds_file):
    _gcp_creds = os.environ.get("GCP_CREDENTIALS", "").strip()
    if _gcp_creds:
        import tempfile
        _tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        _tmp.write(_gcp_creds)
        _tmp.close()
        CREDS_FILE = _tmp.name
    else:
        print("❌ ERROR: GCP credentials not found")
        print("   Local: ~/.claude/credentials/mealplanner-gcp.json")
        print("   Railway: Set GCP_CREDENTIALS variable with JSON content")
        exit(1)

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

RECIPE_GUIDELINES = """
**Estilos de Cocina** (adaptados a necesidades dietéticas):
- LatAm: Comida argentina, mexicana, colombiana, peruana
- Proteínas: pollo, carne, pescado, huevos, legumbres
- Base: arroz, pasta, papas, pan, choclo
- Métodos de cocción: a la parrilla, al horno, hervido, al vapor, salteado (sin freír)
"""


def _render_meal(meal) -> str:
    """Render meal name + nutrition info or fallback to string."""
    if isinstance(meal, dict) and "name" in meal:
        name = meal.get("name", "")
        kcal = meal.get("kcal", "?")
        prot = meal.get("prot_g", "?")
        carb = meal.get("carb_g", "?")
        fat = meal.get("fat_g", "?")
        info = f"<small style='color:#777;display:block;margin-top:3px;font-size:12px;'>{kcal} kcal · Prot {prot}g · Carb {carb}g · Gra {fat}g</small>"
        return f"{name}{info}"
    return str(meal) if meal else ""


def _meal_name(meal) -> str:
    """Extract meal name from structured recipe or plain string."""
    if isinstance(meal, dict) and "name" in meal:
        return meal.get("name", "")
    return str(meal) if meal else ""


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
        bf = _render_meal(meals.get("breakfast", ""))
        ln = _render_meal(meals.get("lunch", ""))
        dn = _render_meal(meals.get("dinner", ""))
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


def generate_meal_plan(client: Anthropic, row_data: dict, last_recipes: str) -> dict:
    """Generate meal plan using Claude API."""
    family_size = row_data.get("family_size", "")
    ages = row_data.get("ages", "")
    restrictions = row_data.get("restrictions", "")
    picky_eaters = row_data.get("picky_eaters", "")
    cooking_time = row_data.get("cooking_time", "")
    preferences = row_data.get("preferences", "")

    avoid_recipes = ""
    if last_recipes:
        avoid_recipes = f"\n**IMPORTANT: Never repeat these meals from last week:**\n{last_recipes}"

    # Interpret dietary restrictions
    dietary_notes = ""
    if restrictions:
        restrictions_lower = restrictions.lower()
        if "celiaco" in restrictions_lower or "sin gluten" in restrictions_lower or "gluten-free" in restrictions_lower:
            dietary_notes += "\n- Todas las recetas DEBEN SER SIN GLUTEN (sin trigo, pasta regular, etc.)"
        if "diabetico" in restrictions_lower or "diabetic" in restrictions_lower:
            dietary_notes += "\n- Enfócate en alimentos BAJO ÍNDICE GLUCÉMICO, evita azúcares refinados y carbohidratos blancos"
        if "vegetarian" in restrictions_lower or "vegetariana" in restrictions_lower:
            dietary_notes += "\n- Solo proteínas vegetarianas (huevos, queso, legumbres, frutos secos)"
        if "vegana" in restrictions_lower or "vegan" in restrictions_lower:
            dietary_notes += "\n- Solo proteínas veganas (legumbres, frutos secos, soya, semillas)"
        if "alergia" in restrictions_lower or "allergy" in restrictions_lower or "alérgico" in restrictions_lower:
            dietary_notes += f"\n- Evita alérgenos comunes mencionados: {restrictions}"
        else:
            dietary_notes += f"\n- Restricciones: {restrictions}"

    health_preference = ""
    if preferences:
        preferences_lower = preferences.lower()
        if "saludable" in preferences_lower or "healthy" in preferences_lower or "liviana" in preferences_lower or "light" in preferences_lower:
            health_preference = "\n- PRIORIZA OPCIONES SALUDABLES: a la parrilla, al horno, al vapor (evita frituras, exceso de aceite, comida rápida)"
        if "casera" in preferences_lower or "home-style" in preferences_lower:
            health_preference += "\n- Enfócate en recetas caseras, estilo comida LatAm tradicional"

    prompt = f"""Genera un plan de comidas personalizado de 7 días estilo LatAm en formato JSON.

PERFIL DE FAMILIA:
- Cantidad: {family_size} personas
- Edades: {ages}
- Come poco: {picky_eaters}
- Tiempo disponible para cocinar: {cooking_time}{dietary_notes}{health_preference}

{RECIPE_GUIDELINES}

{avoid_recipes}

REGLAS DE GENERACIÓN:
1. Crea recetas ORIGINALES adaptadas a sus necesidades dietéticas/salud específicas
2. Cada receta debe respetar todas las restricciones y preferencias
3. Para celíaco: usa alternativas sin gluten
4. Para diabético: alimentos bajos en GI, carbohidratos controlados
5. Para niños o que comen poco: sabores simples, suaves, familiares
6. Mantén comidas bajo 20 minutos si el tiempo de cocina es limitado
7. Sin repetir recetas dentro de los 7 días
8. Reutiliza ingredientes entre comidas para minimizar lista de compras
9. Incluye porciones apropiadas para {family_size} personas
10. Todas las recetas deben ser auténtico estilo LatAm (Argentina, México, Colombia, Perú)
11. CADA RECETA INCLUYE DATOS NUTRICIONALES: estimaciones razonables por porción (kcal, proteínas, carbohidratos, grasas)

CRÍTICO: Retorna SOLO JSON crudo (sin markdown, sin bloques de código, sin acentos graves, sin texto extra). Comienza inmediatamente con {{ y termina con }}. Cada receta es una cadena CORTA (máx 8 palabras).

Formato de ejemplo (sigue exactamente):
{{
  "meal_plan": {{
    "monday": {{"breakfast": {{"name": "Huevos revueltos con pan tostado", "kcal": 320, "prot_g": 18, "carb_g": 22, "fat_g": 14}}, "lunch": {{"name": "Arroz con pollo y verduras", "kcal": 520, "prot_g": 35, "carb_g": 55, "fat_g": 10}}, "dinner": {{"name": "Pechuga a la parrilla con papas", "kcal": 380, "prot_g": 42, "carb_g": 8, "fat_g": 9}}}},
    "tuesday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}},
    "wednesday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}},
    "thursday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}},
    "friday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}},
    "saturday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}},
    "sunday": {{"breakfast": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "lunch": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}, "dinner": {{"name": "...", "kcal": 0, "prot_g": 0, "carb_g": 0, "fat_g": 0}}}}
  }},
  "shopping_list": {{"produce": ["tomate", "cebolla"], "proteins": ["pollo"], "dairy": ["queso"], "pantry": ["arroz"], "frozen": [], "other": []}},
  "meal_prep_tips": ["Prepara verduras el domingo", "Cocina arroz en cantidad"],
  "key_insights": {{"avg_prep_time_mins": 25, "picky_friendly_meals": 18, "ingredient_reuse_count": 8, "healthier_options": 19, "budget_notes": "Ingredientes de temporada"}}
}}"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
    response_text = response_text.strip()

    # Try to parse JSON, with better error handling
    try:
        plan_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from Claude: {e}\nResponse: {response_text[:200]}")

    return plan_data


def send_email_mailjet(to_email: str, subject: str, html_body: str) -> bool:
    """Send email via Mailjet using goplanify.com verified sender."""
    MAILJET_API_KEY = "86e75a4aec95416b39d15f8acb0b037c"
    MAILJET_API_SECRET = "d420a490c00c0f983716e803b0e5272c"

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
            print(f"✅ Email sent to {to_email}")
            return True
        else:
            errors = msg_status.get("Errors", [])
            print(f"❌ Mailjet message error: {errors}")
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

    # Initialize Anthropic client with explicit API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    # If not in env, try to load from ~/.zshrc (for scheduled tasks)
    if not api_key:
        import subprocess
        try:
            result = subprocess.run(
                ['bash', '-c', 'source ~/.zshrc && echo $ANTHROPIC_API_KEY'],
                capture_output=True,
                text=True,
                timeout=5
            )
            api_key = result.stdout.strip()
        except:
            pass

    if not api_key:
        print("❌ ERROR: ANTHROPIC_API_KEY not found")
        print("   Set it with: export ANTHROPIC_API_KEY='your-api-key'")
        return

    client = Anthropic(api_key=api_key)

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

        print(f"🔄 Row {row_idx}: Generating plan for {to_email}...")

        try:
            # Generate plan
            plan_data = generate_meal_plan(client, row_data, last_recipes)

            # Build complete plan
            plan = {
                "submission_id": submission_id,
                "generated_date": datetime.now().strftime("%d/%m/%Y"),
                "parameters": row_data,
                "meal_plan": plan_data["meal_plan"],
                "shopping_list": plan_data["shopping_list"],
                "meal_prep_tips": plan_data["meal_prep_tips"],
                "key_insights": plan_data["key_insights"],
            }

            # Build and send email
            subject = f"🍽️ Tu plan de comidas semanal - {submission_id}"
            html_body = build_html_email(plan)
            success = send_email_mailjet(to_email, subject, html_body)

            if success:
                # Update sheet
                update_sheet_cell(sheets, row_idx, col_to_letter(status_col), "Done")

                # Update last recipes if column exists
                if "last_recipes" in col_map:
                    meals = []
                    for day, meals_day in plan_data["meal_plan"].items():
                        meals.extend([_meal_name(meals_day.get("breakfast", "")), _meal_name(meals_day.get("lunch", "")), _meal_name(meals_day.get("dinner", ""))])
                    meals_str = ", ".join([m for m in meals if m])
                    update_sheet_cell(sheets, row_idx, col_to_letter(col_map.get("last_recipes", 0)), meals_str)

                processed += 1
            else:
                update_sheet_cell(sheets, row_idx, col_to_letter(status_col), "Error: email send failed")
                errors += 1

        except Exception as e:
            print(f"❌ Row {row_idx}: {str(e)}")
            update_sheet_cell(sheets, row_idx, col_to_letter(status_col), f"Error: {str(e)[:50]}")
            errors += 1

    print(f"\n✅ Processing complete: {processed} sent, {errors} errors")


if __name__ == "__main__":
    main()
