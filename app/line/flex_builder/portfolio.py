# app/line/flex_builder/portfolio.py
# 作品集 Carousel 專門檔
# Carousel，包含 3 個作品卡片：
# - 心理諮商地圖 Demo
# - 地政自動化查詢
# - AI 求職經紀人（AI Agent 系統）

# ============
# Flex Card (作品集 carousel)
# ============
def build_portfolio_carousel():
    return {
        "type": "flex",
        "altText": "Sui｜工程作品集",
        "contents": {
            "type": "carousel",
            "contents": [
                # 作品 1：心理諮商地圖 Demo
                {
                    "type": "bubble",
                    ## Hero（封面圖）
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/j8AfACY.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    ## Title + 描述
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
                    ## 透過 message → "心理諮商地圖"
                    ## 作品 → 一鍵 Demo
                    ## 使用者看到 → 點按 → 立即體驗
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
                # 作品 2：地政自動化查詢 Demo
                {
                    "type": "bubble",
                    ## Hero
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/IZkcxQq.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    ## Title
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
                    #Demo 按鈕
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
                # 作品 3：AI 求職經紀人 Demo
                {
                    "type": "bubble",
                    ## Hero
                    "hero": {
                        "type": "image",
                        "url": "https://i.imgur.com/L9uCggH.jpeg",
                        "size": "full",
                        "aspectRatio": "20:13",
                        "aspectMode": "cover",
                    },
                    ## Title 描述
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