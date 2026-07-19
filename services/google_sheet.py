# services/google_sheet.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

def get_sheet_connection():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "credentials.json")
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_path, scope)
    return gspread.authorize(creds)

def get_sheet_data(sheet_id, sheet_name):
    client = get_sheet_connection()
    sh = client.open_by_key(sheet_id)
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_records()