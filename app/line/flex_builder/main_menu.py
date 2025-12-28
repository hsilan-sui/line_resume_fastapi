def build_main_menu_flex():
    def btn(label: str, text: str, style: str = "secondary"):
        return {
            "type": "button",
            "style": style,          # primary | secondary
            "height": "sm",
            "action": {"type": "message", "label": label, "text": text}
        }

    def section_title(t: str):
        return {
            "type": "text",
            "text": t,
            "size": "sm",
            "weight": "bold",
            "color": "#111111",
            "margin": "md"
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
                "spacing": "md",
                "paddingAll": "16px",
                "contents": [
                    # Header
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "xs",
                        "contents": [
                            {"type": "text", "text": "Sui｜互動作品集", "weight": "bold", "size": "xl", "wrap": True},
                            {
                                "type": "text",
                                "text": "點一下就能體驗 Demo（桌機可直接輸入指令）",
                                "size": "sm",
                                "color": "#666666",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": "✨ 推薦先玩：地政查詢 / 諮商資源定位查找",
                                "size": "sm",
                                "color": "#0B6B55",
                                "wrap": True
                            }
                        ]
                    },

                    {"type": "separator", "margin": "md"},

                    # Core actions
                    section_title("🚀 立即體驗"),
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            btn("🗂️ 作品集｜專案作品卡", "作品集", "primary")
                            
                        ]
                    },

                    {"type": "separator", "margin": "md"},

                    # Portfolio / Resume
                    section_title("📌 關於我"),
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            btn("📇 LINE名片｜聯絡方式", "LINE名片", "secondary"),
                        ]
                    },

                    # {"type": "separator", "margin": "md"},

                    # # Links
                    # section_title("🔗 連結"),
                    # {
                    #     "type": "box",
                    #     "layout": "vertical",
                    #     "spacing": "sm",
                    #     "contents": [
                    #         btn("💻 GitHub｜專案 Repo", "GitHub", "secondary"),
                    #         btn("✉️ Email｜104/Cake/Yourator", "Email", "secondary"),
                    #     ]
                    # },
                ]
            },
            "styles": {"body": {"backgroundColor": "#FFFFFF"}}
        }
    }
