def build_landinfo_entry_flex():
    return {
        "type": "flex",
        "altText": "地政圖資查詢 Demo",
        "contents": {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "text", "text": "📌 地政圖資 LINE 自動查詢", "weight": "bold", "size": "lg", "wrap": True},
                    {"type": "text", "text": "📍 暫只支援：桃園市｜復興區 轄區", "size": "sm", "color": "#666666", "wrap": True},
                    {"type": "separator", "margin": "md"},
                    {
                        "type": "text",
                        "text": "💬 打字輸入：地段 地號\n",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "或一鍵跑範例：新光段 549 (以公有地為例) 👇",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True
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
                        "color": "#3B82F6",
                        "height": "sm",
                        "action": {"type": "message", "label": "查詢1 ➡️ 新光段 549", "text": "新光段 549"}
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#3B82F6",
                        "height": "sm",
                        "action": {"type": "message", "label": "查詢2 ➡️ 新光段 477", "text": "新光段 477"}
                        },
                        {
                        "type": "button",
                        "style": "primary",
                        "color": "#3B82F6",
                        "height": "sm",
                        "action": {"type": "message", "label": "查詢3 ➡️ 新光段 478", "text": "新光段 478"}
                        }
                ]
            }
        }
    }
