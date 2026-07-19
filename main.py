import os
import time
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from linebot import LineBotApi
from linebot.models import TextSendMessage
from agent.router import get_ai_response

# 1. 載入環境變數
load_dotenv()

# 2. 初始化 FastAPI
app = FastAPI()

# 3. 獲取 Token 並初始化 LINE API
token = os.getenv('JKqPdMo3B9SDyR9L8sB2rFVquQVO9n5IinedCb0JMylk4w8a+yQk141EiwTWZLxwyoWN0LP+DWlyCgSEILaBzd Vp4d+n1vDCgk2W5YC8SJcuGJ9HNm6MfZ1p3I7axfcFK/HRoX4lv27DiOL5irh1NAdB04t89/1O/w1cDnyilFU=')
if not token:
    # 這行是為了除錯，先暫時把 Token 直接寫在這裡測試看看
    # 如果確定要正式使用，請把這行換成 print 後 exit
    print("錯誤：無法從 .env 讀取到 Token")
    token = "這裡貼上你那串超長的 Token 進行測試" 

line_bot_api = LineBotApi(token)

# 4. 定義路由
@app.post("/callback")
async def callback(request: Request):
    data = await request.json()
    if 'events' in data and len(data['events']) > 0:
        user_id = data['events'][0]['source']['userId']
        user_text = data['events'][0].get('message', {}).get('text', "")
        
        if user_text:
            reply_text = get_ai_response(user_text)
            line_bot_api.push_message(user_id, TextSendMessage(text=reply_text))
            
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)