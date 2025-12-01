# app/line/flex_builder/resume.py

# （Homepage）
# 建立一張「Sui 互動式履歷」的 Flex Bubble，作為LINE OA 的入口頁（Homepage）
## 入口頁（Home Card）
## 自我介紹
## 作品集的主導航 => 所有的 Side Projects 都被包裝成 clickable demo

# ============
# Flex Card (履歷 bubble)
# 整張 Flex Bubble 分成 3 大區：
# Hero（形象照片）
# Body（標題 + 自我介紹）
# Footer（可互動的 Button Group）
# ============
def build_resume_flex():
    flex = {
        "type": "flex",
        "altText": "Sui｜互動式履歷作品集",
        "contents": {
            "type": "bubble",
            "size": "mega",
            # Hero（形象照片）=> 「個人品牌封面」
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/8eOeOZQ.jpeg",
                "size": "full",
                "aspectRatio": "20:13", #適合介於橫幅與方圖間的視覺比例
                "aspectMode": "cover" #讓圖像裁切得乾淨
            },
            ## Body（個人Title & 定位）
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    { # Title & 定位=> 看 1 秒就知道我會做什麼
                        "type": "text",
                        "text": "Sui | Backend × AI × Automation",
                        "weight": "bold",
                        "size": "lg"
                    },
                    { # 小副標（作品集類型）
                        "type": "text",
                        "text": "互動式履歷作品集｜LINE OA",
                        "size": "sm",
                        "color": "#888888",
                        "margin": "sm"
                    },
                    { # 分隔線
                        "type": "separator",
                        "margin": "lg"
                    },
                    { # 自我介紹（重點技能一句話|技能總覽）
                        "type": "text",
                        "text": "特色：FastAPI、Python、自動化、爬蟲、AI Agent、LINE OA 整合",
                        "wrap": True,
                        "size": "sm",
                        "margin": "md"
                    }
                ]
            },
            # Footer（可互動的 Button Group）=> 作品集主功能
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "contents": [
                    # 按鈕 1：查看作品集=> 點了之後 → Bot 回傳“作品集”，觸發你的作品集 Flex menu
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
                    { # 按鈕 2：心理諮商地圖 Demo
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "心理諮商地圖 Demo",
                            "text": "心理諮商地圖"
                        }
                    },
                    {# 按鈕 3：地政查詢 Demo
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