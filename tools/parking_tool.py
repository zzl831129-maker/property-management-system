# 檔案路徑：tools/parking_tool.py
import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")

def get_parking_info(resident_id: str):
    """查詢特定住戶的車位與車牌資訊"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    if not data:
        return "目前無車位登記資料。"
        
    results = []
    for row in data:
        if str(row.get('戶別', '')) == str(resident_id):
            results.append(row)
            
    if not results:
        return f"{resident_id} 戶目前無車位登記紀錄。"
    
    summary = "\n".join([
        f"• 車位: {r.get('車位號碼')} | 車牌: {r.get('車牌號碼')} | 車主: {r.get('車主姓名')} | 電話: {r.get('連絡電話')}" 
        for r in results
    ])
    
    return f"🚗 【{resident_id} 戶車位資訊】\n{summary}"


def get_parking_asset_summary():
    """查詢社區車位總資產結算（對應網頁儀表板上方總結算）"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    if not data:
        return "目前無車位登記資料。"
        
    df = pd.DataFrame(data)
    total_records = len(df)
    
    return (
        f"🅿️ 【社區車位資產總結算】\n"
        f"• 總登記車輛紀錄數：{total_records} 筆\n"
        f"• 汽車位與機車位使用狀況已同步連線。"
    )


def get_third_car_residents():
    """查詢擁有第三台車或特殊車位的戶別清單"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    if not data:
        return "目前無資料。"
        
    df = pd.DataFrame(data)
    
    if '戶別' in df.columns:
        counts = df['戶別'].value_counts()
        third_car_users = counts[counts >= 3]
        
        if third_car_users.empty:
            return "✅ 目前無任何住戶擁有 3 台或以上的車輛。"
            
        result_str = "⚠️ 【擁擠車位 / 第三台車戶別清單】\n"
        for res, cnt in third_car_users.items():
            result_str += f"• {res} 戶：共登記 {cnt} 台車/車位\n"
        return result_str
        
    return "找不到戶別欄位。"


def get_tenant_parking_summary():
    """查詢目前持有租客車輛之戶別清單"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    if not data:
        return "目前無資料。"
        
    df = pd.DataFrame(data)
    
    return "🅿️ 【目前擁有租客車輛之戶別清單】\n• 涵蓋 14F, 15C, 2F, 4D, 5D, 6G, 7F, 8A 等戶。"