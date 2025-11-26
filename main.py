from fastapi import FastAPI, Request
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI LINE Bot is running"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("\n=== 收到 LINE Webhook ===")
    print(json.dumps(body, indent=2, ensure_ascii=False))
    return {"status": "ok"}
