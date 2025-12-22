def build_main_menu_flex():
    def btn(label: str, text: str, style: str = "primary"):
        # style: "primary" | "secondary"
        return {
            "type": "button",
            "style": style,
            "height": "sm",
            "action": {"type": "message", "label": label, "text": text}
        }

    return {
        "type": "flex",
        "altText": "Sui｜互動作品集主選單",
        "contents": {
            "type": "bubble",
            "size": "kilo",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "lg",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {"type": "text", "text": "Sui｜互動作品集", "weight": "bold", "size": "xl"},
                            {
                                "type": "text",
                                "text": "點選直接體驗（桌機也可輸入指令）",
                                "size": "sm",
                                "color": "#666666",
                                "wrap": True
                            },
                        ]
                    },

                    {"type": "separator"},

                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            btn("作品集", "作品集", "primary"),
                            btn("履歷", "履歷", "secondary"),
                        ]
                    },

                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            btn("地政（大利段 1306）", "地政", "secondary"),
                            btn("心理諮商地圖 Demo", "心理諮商", "secondary"),
                        ]
                    },

                    {"type": "separator"},

                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            btn("GitHub", "GitHub", "secondary"),
                            btn("Email", "Email", "secondary"),
                        ]
                    },
                ],
                "paddingAll": "16px"
            },
            "styles": {
                "body": {
                    "backgroundColor": "#FFFFFF"
                }
            }
        }
    }
