from fastapi import FastAPI, Request
from dotenv import load_dotenv
import json
import requests
#import math
import os
import re
# from difflib import SequenceMatcher
from urllib.parse import quote

from app.data.clinic_loader import clinics
from app.utils.geo import geocode, haversine
from app.utils.fuzzy import fuzzy_match
from app.utils.classify import classify_input


load_dotenv()

app = FastAPI()

# ============
# 載入診所資料 => app/data/clinic_loader.py
# ============
# import json

# with open("data/clinic.json", "r") as f:
#     data = json.load(f)

# # ➤ 你的 JSON = 外層 list → 取第一筆 → rows
# if isinstance(data, list) and len(data) > 0 and "rows" in data[0]:
#     clinics = data[0]["rows"]
# else:
#     raise ValueError("clinic.json 格式不符合預期")

# ============
# 基本工具函式
# ============

# def haversine(lat1, lon1, lat2, lon2):
#     R = 6371  # km
#     d_lat = math.radians(lat2 - lat1)
#     d_lon = math.radians(lon2 - lon1)
#     a = (
#         math.sin(d_lat/2)**2
#         + math.cos(math.radians(lat1))
#         * math.cos(math.radians(lat2))
#         * math.sin(d_lon/2)**2
#     )
#     return 2 * R * math.asin(math.sqrt(a))


# def geocode(query: str):
#     url = "https://nominatim.openstreetmap.org/search"
#     params = {"q": query, "format": "json", "limit": 1}

#     r = requests.get(url, params=params)
#     data = r.json()

#     if not data:
#         return None

#     return float(data[0]["lat"]), float(data[0]["lon"])

# def fuzzy_match(keyword: str):
#     results = []
#     for c in clinics:
#         score = SequenceMatcher(None, c["org_name"], keyword).ratio()
#         if score > 0.55:  # 你可以調整
#             results.append((score, c))

#     # 分數高 → 排第一
#     results.sort(reverse=True, key=lambda x: x[0])
#     return [c for _, c in results][:5]

# def classify_input(text: str):
#     if any(k in text for k in ["區", "鄉", "鎮", "市"]):
#         return "district"
#     if any(k in text for k in ["路", "街", "大道", "巷", "號"]):
#         return "address"
#     # 嘗試診所字串比對
#     top = fuzzy_match(text)
#     if top:
#         return "clinic_keyword"
#     return "place"

# ============
# Flex Card ((Upgraded — top 12 clinics))
# ============


import re
from urllib.parse import quote

def build_clinic_flex_item(c):
    # 狀態
    status_text = "有名額" if c["has_quota"] else "無名額"
    status_color = "#4CAF50" if c["has_quota"] else "#F44336"

    tele = "支援遠距" if c.get("teleconsultation") else "無遠距"

    # Google Maps
    address_query = quote(c["address"])
    map_url = f"https://www.google.com/maps/search/?api=1&query={address_query}"

    # ============
    # 電話安全清洗
    # ============
    phone_raw = (c.get("phone") or "").split("、")[0].strip()
    phone_clean = re.sub(r"[^0-9+]", "", phone_raw)
    phone_uri = f"tel:{phone_clean}" if phone_clean else "tel:000"

    # ============
    # 官網 URL fallback（處理 None、空字串、不合法網址）
    # ============
    url = c.get("org_url") or ""
    url = str(url).strip()              # 強制變字串
    if not (url.startswith("http://") or url.startswith("https://")):
        # 用 Google 搜尋診所名稱當 fallback
        url = "https://google.com/search?q=" + quote(c["org_name"])

    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [

                # 標題列
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#22c55e",
                    "paddingAll": "12px",
                    "cornerRadius": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": c["org_name"],
                            "weight": "bold",
                            "size": "lg",
                            "color": "#ffffff"
                        }
                    ]
                },

                # 地址 & 電話
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"📍 {c['address']}",
                            "wrap": True,
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"📞 {c['phone']}",
                            "size": "sm",
                            "color": "#1d4ed8",
                            "action": {
                                "type": "uri",
                                "uri": phone_uri
                            }
                        }
                    ]
                },

                # 狀態列
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"🩺 {status_text}",
                            "color": status_color,
                            "weight": "bold",
                            "size": "sm"
                        },
                        {
                            "type": "text",
                            "text": f"｜ {tele}",
                            "size": "sm",
                            "color": "#6b7280"
                        }
                    ]
                },

                # 名額 badge
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "vertical",
                            "backgroundColor": "#3b82f6",
                            "cornerRadius": "50px",
                            "paddingAll": "6px",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"本週 {c['this_week']}",
                                    "size": "sm",
                                    "color": "#ffffff",
                                    "align": "center"
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "md",
                            "backgroundColor": "#f59e0b",
                            "cornerRadius": "50px",
                            "paddingAll": "6px",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": f"下週 {c['next_week']}",
                                    "size": "sm",
                                    "color": "#ffffff",
                                    "align": "center"
                                }
                            ]
                        }
                    ]
                },

                # 更新日期
                {
                    "type": "text",
                    "text": f"更新：{c['edit_date']}",
                    "size": "xs",
                    "margin": "md",
                    "color": "#9ca3af"
                }
            ]
        },

        # footer: 官網 + 地圖
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#d946ef",
                    "action": {
                        "type": "uri",
                        "label": "官網",
                        "uri": url
                    },
                    "height": "sm"
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "uri",
                        "label": "地圖",
                        "uri": map_url
                    },
                    "height": "sm"
                }
            ]
        }
    }


def build_clinic_flex(results):
    bubbles = [build_clinic_flex_item(c) for c in results[:12]]
    return {
        "type": "flex",
        "altText": "心理諮商診所查詢結果",
        "contents": {
            "type": "carousel",
            "contents": bubbles
        },
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_34_article.png",
                    "action": {
                        "type": "uri",
                        "label": "查找政府合作全台心理諮商網站",
                        "uri": "https://counseling-map.vercel.app/"
                    }
                },
                {
                    "type": "action",
                    "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_17_bookmark.png",
                    "action": {
                        "type": "message",
                        "label": "回到作品集",
                        "text": "作品集"
                    }
                }
            ],
            
        }
    }


def reply_message(reply_token, messages):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('LINE_CHANNEL_ACCESS_TOKEN')}",
    }

    # ⭐ 如果 messages 是 dict（單筆）→ 包成 list
    if isinstance(messages, dict):
        messages = [messages]

    body = {
        "replyToken": reply_token,
        "messages": messages
    }

    res = requests.post(url, headers=headers, json=body)

    print("=== LINE API 回應 ===")
    print(res.status_code)
    print(res.text)

def filter_available(clinic_list):
    return [c for c in clinic_list if c.get("has_quota") is True]


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

        if "作品集" in msg:
            reply_message(reply_token, build_portfolio_carousel())
            return {"ok": True}

        if "心理諮商" in msg or "諮商" in msg:
            reply_message(reply_token, build_counseling_entry())
            return {"ok": True}

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

        reply_message(reply_token, build_resume_flex())
        return {"ok": True}

    return {"ok": True}
