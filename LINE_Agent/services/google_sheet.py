import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_sheet_connection():
    json_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

    if not json_str:
        raise RuntimeError(
            "缺少環境變數 GOOGLE_APPLICATION_CREDENTIALS_JSON"
        )

    try:
        creds_dict = json.loads(json_str)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS_JSON 不是有效 JSON"
        ) from exc

    # 除錯用：確認 Render 實際使用哪一個 Service Account
    print(
        "Google Service Account:",
        creds_dict.get("client_email", "找不到 client_email")
    )

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        scope
    )

    return gspread.authorize(creds)

def get_sheet_data(sheet_id: str, sheet_name: str):
    if not sheet_id:
        raise RuntimeError("缺少環境變數 LEDGER_SHEET_ID")

    try:
        print("準備連線 Google Sheet")
        print("工作表名稱:", sheet_name)

        client = get_sheet_connection()

        print("Google 認證成功，準備開啟試算表")

        spreadsheet = client.open_by_key(sheet_id)

        print("試算表開啟成功:", spreadsheet.title)

        worksheet = spreadsheet.worksheet(sheet_name)

        print("Worksheet 開啟成功:", worksheet.title)

        return worksheet.get_all_records()

    except Exception as exc:
        print(
            "Google Sheet Error:",
            type(exc).__name__,
            str(exc)
        )
        raise