# 檔案路徑：tools/parking_tool.py
import os
import pandas as pd
from services.google_sheet import get_sheet_data

LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")

def get_parking_info(resident_id: str):
    """查詢特定住戶的車位與車牌資訊"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    
    results = []
    for row in data:
        if str(row.get('戶別', '')) == str(resident_id):
            phone = str(row.get('連絡電話', ''))
            if phone and len(phone) < 10:
                phone = phone.zfill(10)
                
            row['聯絡電話'] = phone
            results.append(row)
            
    if not results:
        return f"{resident_id} 戶目前無車位登記紀錄。"
    
    summary = "\n".join([
        f"車位: {r['車位號碼']} | 車牌: {r['車牌號碼']} | 車主: {r['車主姓名']} | 電話: {r['聯絡電話']}" 
        for r in results
    ])
    
    return f"{resident_id} 戶的車位資訊如下：\n{summary}"


def get_parking_asset_summary():
    """查詢社區車位總資產結算與異常清查 (對應網頁儀表板)"""
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    if not data:
        return "目前無車位登記資料。"
        
    df = pd.DataFrame(data)
    
    total_records = len(df)
    # 這裡可以根據您試算表的欄位擴充統計邏輯
    # 例如統計租客、第三台車等
    
    return (
        f"🚗 【社區車位資產總結算】\n"
        f"• 總登記車輛數：{total_records} 筆\n"
        f"• (可在此擴充更多分類統計，如汽車/機車使用率)"
    )