from flask import Flask, request, abort
# 關鍵：加上這行匯入，才能使用 WebhookHandler
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from agent.router import get_ai_response
from config import LINE_ACCESS_TOKEN, LINE_CHANNEL_SECRET

app = Flask(__name__)

# --- 這裡加入除錯用的列印，確認 Secret 有被正確讀取 ---
print(f"DEBUG: CHANNEL_SECRET 是 {LINE_CHANNEL_SECRET}")

# 初始化 API Client
configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
api_client = ApiClient(configuration)
line_bot_api = MessagingApi(api_client)

# 初始化 Handler
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_text = event.message.text.strip()
    reply_text = get_ai_response(user_text)
    
    line_bot_api.reply_message(ReplyMessageRequest(
        replyToken=event.reply_token,
        messages=[TextMessage(text=reply_text)]
    ))

if __name__ == "__main__":
    app.run(port=5000)