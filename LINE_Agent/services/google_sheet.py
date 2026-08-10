import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_connection():
    json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not json_str:
        raise RuntimeError("缺少環境變數 GOOGLE_APPLICATION_CREDENTIALS_JSON")

    try:
        creds_dict = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS_JSON 不是有效 JSON") from exc

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_sheet_data(sheet_id: str, sheet_name: str):
    if not sheet_id:
        raise RuntimeError("缺少環境變數 LEDGER_SHEET_ID")

    client = get_sheet_connection()
    spreadsheet = client.open_by_key(sheet_id)
    worksheet = spreadsheet.worksheet(sheet_name)
    return worksheet.get_all_records()
