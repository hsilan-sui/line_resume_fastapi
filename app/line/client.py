# app/line/client.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ============
# reply_message() — 回送訊息給 LINE 使用者
# 把後端fastapi 要回給 LINE 使用者的訊息，送至 LINE API
# ✔ 呼叫 LINE Messaging API
# ✔ 回覆訊息到使用者
# ✔ 印出 LINE 回應（debug 用）
# ============
def reply_message(reply_token, messages):
    '''
    reply_token（每次使用者訊息 LINE 給你的唯一 token）
    message（文字、Flex、Sticker…
    '''

    # ① 設定 LINE Messaging API 的 endpoint => 回覆訊息必須用 /reply
    url = "https://api.line.me/v2/bot/message/reply"

    # ② 建立 headers（包含你的 Channel Access Token）
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }

    # ③ 若 messages 不是 list，統一轉成 list
    # 因為 LINE API 要求：=> "messages": [ {...}, {...} ]
    # 即使只有一則訊息，也必須用 array 包起來
    if isinstance(messages, dict):
        messages = [messages]

    # ④ 組成回覆 body
    # replyToken 是使用者那則訊息 LINE 給你的(識別)
    # 沒有這個 token → 無法回覆（會 400）。
    body = {
        "replyToken": reply_token,
        "messages": messages
    }

    # ⑤ 發送 POST 請求到 LINE 伺服器
    res = requests.post(url, headers=headers, json=body)

    # ⑥ 印出 API 回應（debug 用）
    print("=== (已拆分結構) LINE API 回應 ===")
    print(res.status_code)
    print(res.text)