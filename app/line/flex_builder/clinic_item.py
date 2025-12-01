# app/line/flex_builder/clinic_item.py
# 將一筆診所資料轉換為完整的 Flex Bubble UI
# 接收一個診所資料 dict，組成一張完整的 LINE Flex Bubble 卡片，可用在 carousel
# 所有的診所資料源都來自我整理過的 data/clinic.json

import re
from urllib.parse import quote

# ============
# Flex Card (單一診所 bubble => 單ㄧ診所卡片 UI 工廠
# ============
# 讓使用者在 LINE 上看到：
# - 診所名稱
# - 地址
# - 電話（可直接點擊撥打）
# - 本週 / 下週名額(badge)
# - 地圖導航
# - Footer 按鈕官網連結
# 讓心理諮商地圖能「在 LINE 裡直接查詢」，不用再跳網站
# ============

def build_clinic_flex_item(c):
    # 狀態 => 讓用戶一眼判斷現在能不能預約 
    # 依據診所是否有名額，決定文字與顏色
    status_text = "有名額" if c["has_quota"] else "無名額"
    status_color = "#4CAF50" if c["has_quota"] else "#F44336"

    # 顯示是否支援遠距心理諮商
    tele = "支援遠距" if c.get("teleconsultation") else "無遠距"

    # Google Maps 連結 => 生成可點擊的 Google Maps 導航(使用者在 LINE 能「一鍵導航」)
    # 對地址 URL encode 後拼成官方 map search URL
    address_query = quote(c["address"])
    map_url = f"https://www.google.com/maps/search/?api=1&query={address_query}"

    # ============
    # 電話安全清洗 => 把診所電話變成可以點擊撥打的格式
    # 取第一個電話（有些有「、」分隔）
    # 移除中文字、空白、特殊符號＝只保留數字
    # 產生 tel: protocol
    # ============
    phone_raw = (c.get("phone") or "").split("、")[0].strip()
    phone_clean = re.sub(r"[^0-9+]", "", phone_raw)
    phone_uri = f"tel:{phone_clean}" if phone_clean else "tel:000"

    # ============
    # 確保官網按鈕一定能用 => 官網 URL fallback（處理 None、空字串、不合法網址）
    # 果不是 → 改用 Google 搜尋診所名稱
    # ============
    url = c.get("org_url") or ""
    url = str(url).strip()              # 強制變字串
    if not (url.startswith("http://") or url.startswith("https://")):
        # 用 Google 搜尋診所名稱當 fallback
        url = "https://google.com/search?q=" + quote(c["org_name"])

    # 回傳Bubble  UI 
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                ### 標題列 => 顯示診所名稱（綠底白字）
                {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#22c55e",
                    "paddingAll": "12px",
                    "cornerRadius": "md",
                    "contents": [ # 內容
                        {
                            "type": "text",
                            "text": c["org_name"],
                            "weight": "bold",
                            "size": "lg",
                            "color": "#ffffff"
                        }
                    ]
                },

                ### 地址 & 電話 =>顯示地址、電話；電話可點擊
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

                ### 狀態列（有名額 / 遠距）
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

                ### 名額 badge(兩個badge)
                {
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        ### 藍色 = 本週 badge
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
                        ### 橘色 = 下週 badge
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

                ### 更新日期 => 讓使用者知道資料新不新
                {
                    "type": "text",
                    "text": f"更新：{c['edit_date']}",
                    "size": "xs",
                    "margin": "md",
                    "color": "#9ca3af"
                }
            ]
        },

        ### footer: 官網 + 地圖 => 提供 CTA（Call-to-Action）
        # 每張卡至少要有兩個可操作動作
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