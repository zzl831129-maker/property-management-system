# main.py
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

# 專門給 LINE 核實用的 GET 請求
@app.get("/callback")
async def verify():
    print("收到 GET 核實請求")
    return {"status": "ok"}

# 專門給 LINE 發訊息用的 POST 請求
@app.post("/callback")
async def handle_message(request: Request):
    data = await request.json()
    print(f"收到訊息: {data}")
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

    @app.api_route("/{path:path}", methods=["GET", "POST"])
async def catch_all(path: str, request: Request):
    print(f"收到不明請求: {request.method} /{path}")
    return {"status": "ok"}