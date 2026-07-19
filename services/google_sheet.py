import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_connection():
    # 1. 直接讀取環境變數
    json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    # 2. 將 JSON 字串轉為字典 (dict)
    creds_dict = json.loads(json_str)
    
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    
    # 3. 關鍵修正：使用 from_json_keyfile_dict 讀取字典，而不是讀取檔案路徑
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    
    return gspread.authorize(creds)

def get_sheet_data(sheet_id, sheet_name):
    client = get_sheet_connection()
    sh = client.open_by_key(sheet_id)
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_records()