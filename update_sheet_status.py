"""
Run this script once the Google Sheets API is enabled in the GCP project:
https://console.developers.google.com/apis/api/sheets.googleapis.com/overview?project=475039353649

Also share the spreadsheet with: mealplanner@mealplanner-493718.iam.gserviceaccount.com (Editor)

Usage:
  pip install google-auth google-auth-httplib2 google-api-python-client
  python3 scripts/update_sheet_status.py
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDS_FILE = os.path.expanduser("~/.claude/credentials/mealplanner-gcp.json")
SPREADSHEET_ID = "1O6DC-6u5Y642c1v8LkwSYkj9lBGDy_szSLnM0PfucFM"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
sheets = build("sheets", "v4", credentials=creds)

# Read current data to find the status column and unprocessed rows
result = sheets.spreadsheets().values().get(
    spreadsheetId=SPREADSHEET_ID, range="A1:Z"
).execute()
rows = result.get("values", [])

if not rows:
    print("Sheet is empty.")
    exit(0)

headers = rows[0]
status_col = None
for i, h in enumerate(headers):
    if h.strip().lower() == "status":
        status_col = i
        break

if status_col is None:
    # Add status column at the end
    status_col = len(headers)
    col_letter = chr(ord("A") + status_col)
    sheets.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{col_letter}1",
        valueInputOption="RAW",
        body={"values": [["status"]]}
    ).execute()
    print(f"Added 'status' column at position {col_letter}")

col_letter = chr(ord("A") + status_col)

for row_idx, row in enumerate(rows[1:], start=2):
    current_status = row[status_col] if len(row) > status_col else ""
    if current_status in ("", None):
        submission_id = row[0] if row else "unknown"
        cell = f"{col_letter}{row_idx}"
        sheets.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=cell,
            valueInputOption="RAW",
            body={"values": [["Done"]]}
        ).execute()
        print(f"Marked row {row_idx} (Submission: {submission_id}) as Done")
    else:
        print(f"Row {row_idx} already has status: {current_status}")

print("Done.")
