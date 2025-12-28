# 建立 webhook router
from fastapi import APIRouter, Request
import json

from app.data.clinic_loader import clinics
from app.utils.geo import geocode, haversine
from app.utils.fuzzy import fuzzy_match
from app.utils.classify import classify_input
from app.line.client import reply_message

from app.line.flex_builder.main_menu import build_main_menu_flex
#from app.line.flex_builder.clinic_item import build_clinic_flex_item # 診所單張卡片
from app.line.flex_builder.clinic_list import build_clinic_flex, filter_available # 12張診所清單(已引入# 診所單張卡片)
from app.line.flex_builder.resume import build_resume_flex # (履歷 bubble)
from app.line.flex_builder.portfolio import build_portfolio_carousel # 作品集 Carousel
from app.line.flex_builder.portfolio import build_portfolio_carousel
from app.line.flex_builder.counseling import build_counseling_demo_messages
from app.handlers.landinfo_chat import handle_landinfo_chat

from app.line.flex_builder.landinfo_entry_flexmsg import build_landinfo_entry_flex
# 底部快速回覆鍵
from app.line.quickbtn.landinfo_quickreply import build_landinfo_quickreply

router = APIRouter()

MOHW_URL = "https://www.mohw.gov.tw/cp-16-79408-1.html"

def ensure_list(payload):
    return payload if isinstance(payload, list) else [payload]


def build_result_quickreply_text():
    """
    Do what: 看完 12 張清單後，還能再查一次 / 回入口 / 回作品集
    How: 用「文字訊息」掛 quickReply(location)
    Why: location quickReply 掛在 flex 可能 400；掛在 text 最穩
    """
    return {
        "type": "text",
        "text": "想繼續操作？",
        "quickReply": {
            "items": [
                {"type": "action", "action": {"type": "location", "label": "再查一次(重傳定位)"}},
                {"type": "action", "action": {"type": "message", "label": "🟡 回查找入口", "text": "心理諮商資源查找"}},
                {"type": "action", "action": {"type": "message", "label": "🟢 回作品集", "text": "作品集"}},
            ]
        }
    }



@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("\n=== 收到 LINE Webhook ===")
    print(json.dumps(body, indent=2, ensure_ascii=False))

    event = body["events"][0]
    event_type = event["type"]
    reply_token = event.get("replyToken")

    # Follow 事件 → 回 2 則訊息（文字保底 + Flex 主選單）
    if event_type == "follow":
        welcome_text = (
            "嗨，我是 Sui，這支 LINE 是「可體驗的互動作品集」。\n\n"
            "輸入：\n"
            "作品集 － 看所有 Demo\n"
            "履歷 － 履歷卡\n"
            "地政 － 立即體驗查詢（大利段 1306）\n"
            "心理諮商 － 開地圖 Demo\n"
            "GitHub － 專案連結\n"
            "Email － 聯絡我（含 104/Cake/Yourator）"
        )

        reply_message(reply_token, [
            {"type": "text", "text": welcome_text},
            build_main_menu_flex()
        ])
        return {"ok": True}

    # 1️⃣ 忽略非 message event
    if event_type != "message":
        print(f"👉 忽略非 message 事件：{event_type}")
        return {"ok": True}

    message = event["message"]
    msg_type = message["type"]

    # -------------------------------------------------
    # 2️⃣ 定位 → 最近 12 間 + 結果 quickReply（用 text 掛）
    # -------------------------
    if msg_type == "location":
        user_lat = message["latitude"]
        user_lng = message["longitude"]

        ranked = sorted(clinics, key=lambda c: haversine(user_lat, user_lng, c["lat"], c["lng"]))
        available = filter_available(ranked)

        payload = ensure_list(build_clinic_flex(available))

        # ✅ 保證最後一則是 quickReply text，且總數不超過 5
        qr_msg = build_result_quickreply_text()
        if len(payload) >= 5:
            payload = payload[:4] + [qr_msg]   # 留 4 則 + quickReply
        else:
            payload.append(qr_msg)

        reply_message(reply_token, payload)
        return {"ok": True}



    # -------------------------------------------------
    # 3️⃣ 處理文字
    # -------------------------------------------------
    if msg_type == "text":
        raw = message["text"]

        # ✅ 給解析用：保留空白（地政會用到）
        msg_text = raw.strip().replace("\u200b", "").replace("\n", "")

        # ✅ 給指令比對用：去空白（HR 點按鈕/打字都穩）
        msg_key = msg_text.replace(" ", "")

        print(f"👉 使用者訊息 msg_text={msg_text} | msg_key={msg_key}")

        # =========================
        # ✅ 指令路由表（只處理「固定指令」）
        # =========================
        COMMAND_ROUTES = {
            "作品集": lambda: build_portfolio_carousel(),
            "履歷": lambda: build_resume_flex(),
            "LINE名片": lambda: build_resume_flex(),
            "menu": lambda: build_main_menu_flex(),

            # ✅ 心理諮商 Demo（入口卡）
            # "全台心理諮商診所": lambda: build_counseling_demo_messages(),
            # "心理諮商": lambda: build_counseling_demo_messages(),
            # "諮商": lambda: build_counseling_demo_messages(),
            "心理諮商資源查找": lambda: build_counseling_demo_messages(),

            # 方案說明（回文字連結）
            "衛福部方案說明": lambda: {
                "type": "text",
                "text": f"衛福部｜15–45歲心理健康支持方案（官方說明）：\n{MOHW_URL}"
            },

            # ✅ 這顆按鈕建議：直接引導「可貼上的 demo 指令」
            # （如果你已經有 build_landinfo_demo_flex 且不需 BASE_URL，就改成回 flex）
            # "地政": lambda: {
            #     "type": "text",
            #     "text": "💬 請輸入：地段 地號（或點擊⤵️直接跑範例：新光段 549）",
            #     "quickReply": build_landinfo_quickreply(),
            # },
            "地政": lambda: {
                "type": "flex",
                "altText": "地政圖資查詢 Demo",
                "contents": build_landinfo_entry_flex()["contents"],
                "quickReply": build_landinfo_quickreply(),
            },

            "露營票務系統": lambda: {
                "type": "text",
                "text": "🎟 Everforest 活動票務系統（Backend）\n亮點：額滿控制 / 訂單流程 / 通知\nRepo：<貼連結>"
            },

            "LINEOA": lambda: {
                "type": "text",
                "text": "🤖 LINE OA 互動作品集（FastAPI）\nFollow 歡迎訊息＋主選單 Flex＋Demo 指令導流。\nRepo：<貼連結>"
            },
            "LINEOA作品集": lambda: {
                "type": "text",
                "text": "🤖 LINE OA 互動作品集（FastAPI）\nRepo：<貼連結>"
            },

            "GitHub": lambda: {"type": "text", "text": "GitHub：<貼你的 GitHub>"},
            "Email": lambda: {"type": "text", "text": "Email：<貼你的 email>\n104/Cake/Yourator：<貼連結或一句話>"},
        }

        # 1) ✅ 先走「固定指令」路由（按鈕一定會命中）
        if msg_key in COMMAND_ROUTES:
            payload = COMMAND_ROUTES[msg_key]()
            reply_message(reply_token, ensure_list(payload))  # ✅ 統一 list
            return {"ok": True}

        # 2) ✅ 再交給地政聊天解析（重點：用 msg_text，不要用 msg_key）
        if await handle_landinfo_chat(event, reply_token, msg_text):
            return {"ok": True}

        # 3) ✅ 最後才跑你原本的診所分類（同樣建議用 msg_text）
        qtype = classify_input(msg_text)
        print(f"👉 判斷輸入類型：{qtype}")

        if qtype == "clinic_keyword":
            matched = fuzzy_match(msg_text)
            available = filter_available(matched)
            reply_message(reply_token, build_clinic_flex(available))
            return {"ok": True}

        if qtype in ["district", "address", "place"]:
            coords = geocode(msg_text)
            if not coords:
                reply_message(reply_token, [{"type": "text", "text": "找不到這個地點，試另一種說法？"}])
                return {"ok": True}

            lat, lng = coords
            ranked = sorted(clinics, key=lambda c: haversine(lat, lng, c["lat"], c["lng"]))
            available = filter_available(ranked)

            payload = ensure_list(build_clinic_flex(available))

            qr_msg = build_result_quickreply_text()
            if len(payload) >= 5:
                payload = payload[:4] + [qr_msg]
            else:
                payload.append(qr_msg)

            reply_message(reply_token, payload)
            return {"ok": True}

        return {"ok": True}
    return {"ok": True}

