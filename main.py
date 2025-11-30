from fastapi import FastAPI, Request
import json
from dotenv import load_dotenv
import requests
import math
import os
from difflib import SequenceMatcher
from urllib.parse import quote


load_dotenv()

app = FastAPI()

# ============
# 載入診所資料
# ============
with open("data/clinic.json", "r") as f:
    data = json.load(f)

# ➤ 你的 JSON = 外層 list → 取第一筆 → rows
if isinstance(data, list) and len(data) > 0 and "rows" in data[0]:
    clinics = data[0]["rows"]
else:
    raise ValueError("clinic.json 格式不符合預期")

# ============
# 基本工具函式
# ============

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat/2)**2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon/2)**2
    )
    return 2 * R * math.asin(math.sqrt(a))


def geocode(query: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "json", "limit": 1}

    r = requests.get(url, params=params)
    data = r.json()

    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])

def fuzzy_match(keyword: str):
    results = []
    for c in clinics:
        score = SequenceMatcher(None, c["org_name"], keyword).ratio()
        if score > 0.55:  # 你可以調整
            results.append((score, c))

    # 分數高 → 排第一
    results.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in results][:5]

def classify_input(text: str):
    if any(k in text for k in ["區", "鄉", "鎮", "市"]):
        return "district"
    if any(k in text for k in ["路", "街", "大道", "巷", "號"]):
        return "address"
    # 嘗試診所字串比對
    top = fuzzy_match(text)
    if top:
        return "clinic_keyword"
    return "place"

# ============
# Flex Card ((Upgraded — top 12 clinics))
# ============
def build_clinic_flex(results):
    bubbles = []
    
    # LINE Carousel 上限：12 個 bubbles
    top_results = results[:12]

    for c in top_results:
        # 使用完整地址提高導航精準度
        address_query = quote(c["address"])
        map_url = f"https://www.google.com/maps/search/?api=1&query={address_query}"

        bubble = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": c["org_name"],
                        "weight": "bold",
                        "size": "lg",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": c["address"],
                        "wrap": True,
                        "size": "sm",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": f"電話：{c.get('phone', '無')}",
                        "size": "sm",
                        "margin": "sm"
                    },
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "導航到這裡",
                            "uri": map_url
                        }
                    }
                ]
            }
        }

        bubbles.append(bubble)

    # 最終回傳 Carousel（最多 12 個）
    return {
        "type": "flex",
        "altText": "心理諮商診所查詢結果",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        }
    }


def reply_message(reply_token, messages):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }

    body = {
        "replyToken": reply_token,
        "messages": messages
    }

    res = requests.post(url, headers=headers, json=body)

    print("=== LINE API 回應 ===")
    print(res.status_code)
    print(res.text)


def build_resume_flex():
    flex = {
        "type": "flex",
        "altText": "Sui｜互動式履歷作品集",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/8eOeOZQ.jpeg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "Sui | Backend × AI × Automation",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": "互動式履歷作品集｜LINE OA",
                        "size": "sm",
                        "color": "#888888",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "lg"
                    },
                    {
                        "type": "text",
                        "text": "特色：FastAPI、Python、自動化、爬蟲、AI Agent、LINE OA 整合",
                        "wrap": True,
                        "size": "sm",
                        "margin": "md"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "查看作品集",
                            "text": "作品集"
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "心理諮商地圖 Demo",
                            "text": "心理諮商地圖"
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "地政查詢 Demo",
                            "text": "地政查詢"
                        }
                    }
                ],
                "flex": 0
            }
        }
    }
    return flex


def build_portfolio_carousel():
    return {
        "type": "flex",
        "altText": "Sui｜工程作品集",
        "contents": {
            "type": "carousel",
            "contents": [
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/j8AfACY.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "心理諮商地圖 Demo", "weight": "bold", "size": "lg"},
                            {
                                "type": "text",
                                "text": "Next.js + Leaflet + Redis Queue\n全台 614 間合作心理諮商診所地圖",
                                "size": "sm",
                                "wrap": True,
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "action": {"type": "message", "label": "查看 Demo", "text": "心理諮商地圖"}
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/IZkcxQq.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "地政自動化查詢", "weight": "bold", "size": "lg"},
                            {
                                "type": "text",
                                "text": "Playwright + Cloud Run\n自動查詢段名地號，擷取謄本與地籍圖",
                                "size": "sm",
                                "wrap": True,
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "action": {"type": "message", "label": "查看 Demo", "text": "地政查詢"}
                            }
                        ]
                    }
                },
                {
                    "type": "bubble",
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/L9uCggH.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {"type": "text", "text": "AI 求職經紀人", "weight": "bold", "size": "lg"},
                            {
                                "type": "text",
                                "text": "CrewAI + LangGraph\n自動找職缺、產履歷、追蹤投遞進度。",
                                "size": "sm",
                                "wrap": True,
                                "margin": "md"
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "button",
                                "action": {"type": "message", "label": "查看 Demo", "text": "AI 求職經紀人"}
                            }
                        ]
                    }
                }
            ]
        }
    }



def build_counseling_entry():
    return {
        "type": "flex",
        "altText": "心理諮商地圖",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/Zaa9d8R.jpeg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "心理諮商診所查詢",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "text",
                        "text": "支援：最近診所、地址查詢、縣市查詢",
                        "wrap": True,
                        "size": "sm",
                        "color": "#666666",
                        "margin": "md"
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "text",
                        "text": "請點下方按鈕：",
                        "size": "sm",
                        "margin": "md",
                        "color": "#444444"
                    },
                    {
                        "type": "text",
                        "text": "① 傳送定位 → 找最近診所\n② 輸入地址 → 找附近診所\n③ 輸入縣市 → 查該地區診所",
                        "size": "sm",
                        "wrap": True,
                        "margin": "sm",
                        "color": "#555555"
                    }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "message",
                            "label": "傳送我的定位",
                            "text": "請按上方 quick reply 傳送定位"
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "action": {
                            "type": "uri",
                            "label": "查看完整地圖",
                            "uri": "https://counseling-map.vercel.app/"
                        }
                    }
                ]
            }
        },
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_24_location.png",
                    "action": {"type": "location", "label": "傳送我的定位"}
                }
            ]
        }
    }



@app.get("/")
async def root():
    return {"message": "FastAPI LINE Bot is running"}


@app.post("/webhook")
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

        # ⭐ 直接給全部（build_clinic_flex會自動限制12）
        reply_message(reply_token, [build_clinic_flex(ranked)])
        return {"ok": True}

    # -------------------------------------------------
    # 3️⃣ 處理文字
    # -------------------------------------------------
    if msg_type == "text":
        raw = message["text"]
        msg = raw.strip().replace("\u200b", "").replace("\n", "")

        print(f"👉 使用者訊息：{msg}")

        if "作品集" in msg:
            reply_message(reply_token, [build_portfolio_carousel()])
            return {"ok": True}

        if "心理諮商" in msg or "諮商" in msg:
            reply_message(reply_token, [build_counseling_entry()])
            return {"ok": True}

        qtype = classify_input(msg)
        print(f"👉 判斷輸入類型：{qtype}")

        # 模糊診所名稱 → 已經會抓前 5（可改 12）
        if qtype == "clinic_keyword":
            matched = fuzzy_match(msg)
            reply_message(reply_token, [build_clinic_flex(matched)])
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

            reply_message(reply_token, [build_clinic_flex(ranked)])
            return {"ok": True}

        reply_message(reply_token, [build_resume_flex()])
        return {"ok": True}

    return {"ok": True}
