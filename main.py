import os
import time
from fastapi import FastAPI, Request
from linebot import LineBotApi
from linebot.models import TextSendMessage
from agent.router import get_ai_response

# 1. 初始化 FastAPI
app = FastAPI()

token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(token)

line_bot_api = LineBotApi(token)

# 2. 定義路由
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