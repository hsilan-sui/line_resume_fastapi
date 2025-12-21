# 建立 webhook router
from fastapi import APIRouter, Request
import json

from app.data.clinic_loader import clinics
from app.utils.geo import geocode, haversine
from app.utils.fuzzy import fuzzy_match
from app.utils.classify import classify_input
from app.line.client import reply_message

#from app.line.flex_builder.clinic_item import build_clinic_flex_item # 診所單張卡片
from app.line.flex_builder.clinic_list import build_clinic_flex, filter_available # 12張診所清單(已引入# 診所單張卡片)
from app.line.flex_builder.resume import build_resume_flex # (履歷 bubble)
from app.line.flex_builder.portfolio import build_portfolio_carousel # 作品集 Carousel
from app.line.flex_builder.counseling import build_counseling_entry # 查詢最近的心理諮商診所

from app.line.flex_builder.landinfo_demo import build_landinfo_demo_flex

from app.handlers.landinfo_chat import handle_landinfo_chat


router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("\n=== 收到 LINE Webhook ===")
    print(json.dumps(body, indent=2, ensure_ascii=False))

    event = body["events"][0]
    event_type = event["type"]
    reply_token = event.get("replyToken")

    # 1️⃣ 忽略非 message event
    if event_type != "message":
        print(f"👉 忽略非 message 事件：{event_type}")
        return {"ok": True}

    message = event["message"]
    msg_type = message["type"]

    # -------------------------------------------------
    # 2️⃣ 處理定位 → 回傳最近 12 間
    # -------------------------------------------------
    if msg_type == "location":
        user_lat = message["latitude"]
        user_lng = message["longitude"]

        ranked = sorted(
            clinics,
            key=lambda c: haversine(user_lat, user_lng, c["lat"], c["lng"])
        )

        available = filter_available(ranked)     # ⭐ 只保留有名額


    
        # ⭐ 直接給全部（build_clinic_flex會自動限制12）
        reply_message(reply_token, build_clinic_flex(available))

        return {"ok": True}

    # -------------------------------------------------
    # 3️⃣ 處理文字
    # -------------------------------------------------
    if msg_type == "text":
        raw = message["text"]
        msg = raw.strip().replace("\u200b", "").replace("\n", "")

        print(f"👉 使用者訊息：{msg}")

        if await handle_landinfo_chat(event, reply_token, msg):
            return {"ok": True}

        if "作品集" in msg:
            reply_message(reply_token, build_portfolio_carousel())
            return {"ok": True}

        if "履歷" in msg:
            reply_message(reply_token, build_resume_flex())
            return {"ok": True}

        if "心理諮商" in msg or "諮商" in msg:
            reply_message(reply_token, build_counseling_entry())
            return {"ok": True}
        
        # 4️⃣ 地政 Demo ----
        # if "地政" in msg: 
        #     # 你的 FastAPI 網域（要記得改成自己的）
        #     BASE_URL = "https://f00f5389755a.ngrok-free.app"
        #     flex = build_landinfo_demo_flex(BASE_URL)
        #     reply_message(reply_token, flex)
        #     return {"ok": True}

        qtype = classify_input(msg)
        print(f"👉 判斷輸入類型：{qtype}")

        # 模糊診所名稱 → 已經會抓前 5（可改 12）
        if qtype == "clinic_keyword":
            matched = fuzzy_match(msg)
            available = filter_available(matched)    # ⭐ 只保留有名額
            reply_message(reply_token, build_clinic_flex(available))
            return {"ok": True}

        # 地址 / 行政區 / 地標 → 回傳最近 12 間
        if qtype in ["district", "address", "place"]:
            coords = geocode(msg)
            if not coords:
                reply_message(reply_token, [{
                    "type": "text",
                    "text": "找不到這個地點，試另一種說法？"
                }])
                return {"ok": False}

            lat, lng = coords
            ranked = sorted(
                clinics,
                key=lambda c: haversine(lat, lng, c["lat"], c["lng"])
            )

            available = filter_available(ranked)     # ⭐ 只保留有名額

            reply_message(reply_token, build_clinic_flex(available))
            return {"ok": True}


    return {"ok": True}
