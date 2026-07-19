# tools/parking_tool.py
from services.google_sheet import get_sheet_data
import os
LEDGER_SHEET_ID = os.getenv("LEDGER_SHEET_ID")

def get_parking_info(resident_id: str):
    data = get_sheet_data(LEDGER_SHEET_ID, "車位登記")
    
    results = []
    for row in data:
        if str(row.get('戶別', '')) == str(resident_id):
            # 強制將電話補齊：如果總長度小於 10，前面補 0
            phone = str(row.get('連絡電話', ''))
            if phone and len(phone) < 10:
                phone = phone.zfill(10) # 確保變成 09XXXXXXXX 的格式
                
            row['聯絡電話'] = phone # 存回 row 裡面
            results.append(row)
            
    if not results:
        return f"{resident_id} 戶目前無車位登記紀錄。"
    
    # 加入連絡電話欄位到 AI 的回覆中
    summary = "\n".join([
        f"車位: {r['車位號碼']} | 車牌: {r['車牌號碼']} | 車主: {r['車主姓名']} | 電話: {r['聯絡電話']}" 
        for r in results
    ])
    
    return f"{resident_id} 戶的車位資訊如下：\n{summary}"