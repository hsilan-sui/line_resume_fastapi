# app/line/flex_builder/portfolio.py
# 作品集 Carousel 專門檔
# Carousel，包含 3 個作品卡片：
# - 心理諮商地圖 Demo
# - 地政自動化查詢
# - AI 求職經紀人（AI Agent 系統）



# app/line/flex_builder/portfolio.py
def build_role_badge(text: str, bg: str = "#111827"):
    text = text.strip()

    # 依字長調整膠囊寬（你原本的邏輯保留）
    width = "56px"
    if len(text) >= 6:
        width = "92px"
    elif len(text) >= 4:
        width = "72px"

    return {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": text,
                "align": "center",
                "size": "xs",
                "color": "#FBFBFF",
                "weight": "bold",
                "wrap": False
            }
        ],
        "position": "absolute",
        "cornerRadius": "20px",
        "offsetTop": "14px",
        "offsetStart": "14px",
        "backgroundColor": bg,

        # ✅ 關鍵：用 padding 撐高度，比 height 穩
        "paddingAll": "4px",

        # ✅ 關鍵：置中（跟你 resume 同招）
        "justifyContent": "center",
        "alignItems": "center",

        # ✅ 保留固定寬度（你想要一致就留）
        "width": width
    }




# ✅ 圖片 + 左上角 badge（同一個 box 內才能疊上去）
def build_image_header(image_url: str, badge_text: str, badge_bg: str = "#111827"):
    return {
        "type": "box",
        "layout": "vertical",
        "paddingAll": "0px",
        "contents": [
            {
                "type": "image",
                "url": image_url,
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
                "gravity": "top"
            },
            build_role_badge(badge_text, badge_bg)
        ]
    }

def build_portfolio_carousel():
    return {
        "type": "flex",
        "altText": "Sui｜專案作品集",
        "contents": {
            "type": "carousel",
            "contents": [
                # 作品 1：地政自動化查詢 Demo
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "0px",
                        "contents": [
                            build_image_header(
                                "https://i.imgur.com/IZkcxQq.jpeg",
                                "後端 Node.js ",
                                "#FF4D8D"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "地政自動化查詢", "weight": "bold", "size": "lg"},
                                    {
                                        "type": "text",
                                        "text": "Playwright + Cloud Run\n自動查詢段名地號，擷取謄本與地籍圖",
                                        "size": "sm",
                                        "wrap": True,
                                        "color": "#666666"
                                    },
                                ]
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
                                "action": {"type": "message", "label": "查看 Demo", "text": "地政"}
                            }
                        ]
                    }
                },

                # 作品 2：心理諮商地圖 Demo
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "0px",
                        "contents": [
                            build_image_header(
                                "https://i.imgur.com/j8AfACY.jpeg",
                                "前端 Next.js",
                                "#01B468"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "心理諮商地圖 Demo", "weight": "bold", "size": "lg"},
                                    {
                                        "type": "text",
                                        "text": "Next.js + Leaflet + Redis Queue\n全台 614 間合作心理諮商診所地圖",
                                        "size": "sm",
                                        "wrap": True,
                                        "color": "#666666"
                                    },
                                ]
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
                                "action": {"type": "message", "label": "查看 Demo", "text": "全台心理諮商診所"}
                            }
                        ]
                    }
                },

                # 作品 3：Everforest 活動票務系統（Backend）
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "0px",
                        "contents": [
                            build_image_header(
                                "https://i.imgur.com/L9uCggH.jpeg",
                                "後端 Node.js",
                                "#FF4D8D"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "Everforest 活動票務系統（Backend）", "weight": "bold", "size": "lg"},
                                    {
                                        "type": "text",
                                        "text": "Node.js + Express + PostgreSQL\n活動管理、購票下單、額滿控制、訂單通知",
                                        "size": "sm",
                                        "wrap": True,
                                        "color": "#666666"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Tech：TypeORM｜JWT (HttpOnly Cookie)｜Docker｜Swagger",
                                        "size": "xs",
                                        "wrap": True,
                                        "color": "#999999"
                                    }
                                ]
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
                                "action": {"type": "message", "label": "查看 Demo", "text": "露營票務系統"}
                            }
                        ]
                    }
                },
                # 作品 4：LINE OA 互動作品集（FastAPI）
                {
                    "type": "bubble",
                    "size": "kilo",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "0px",
                        "contents": [
                            build_image_header(
                                "https://i.imgur.com/xxxxxxx.jpeg",  # 先隨便放一張，之後換成你的截圖
                                "後端 FastAPI",
                                "#FF4D8D"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "LINE OA 互動作品集（FastAPI）", "weight": "bold", "size": "lg"},
                                    {
                                        "type": "text",
                                        "text": "Follow 歡迎訊息＋主選單 Flex\n整合作品入口與 Demo 指令流程",
                                        "size": "sm",
                                        "wrap": True,
                                        "color": "#666666"
                                    },
                                    {
                                        "type": "text",
                                        "text": "Tech：FastAPI｜LINE Messaging API｜Flex Message",
                                        "size": "xs",
                                        "wrap": True,
                                        "color": "#999999"
                                    }
                                ]
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
                                "action": {"type": "message", "label": "查看說明", "text": "LINE OA"}
                            }
                        ]
                    }
                }
            ]
        }
    }


# # ====
# # 產生badge helper
# # ====

# def build_role_badge(text: str, bg: str = "#111827"):
#     # text: "前端" | "後端" | "Full-stack"
#     width = "56px"
#     if len(text) >= 6:   # 避免英文或較長字
#         width = "92px"
#     elif len(text) >= 4:
#         width = "72px"

#     return {
#         "type": "box",
#         "layout": "vertical",
#         "contents": [{
#             "type": "text",
#             "text": text,
#             "color": "#ffffff",
#             "align": "center",
#             "size": "xs",
#             "offsetTop": "3px",
#             "weight": "bold"
#         }],
#         "position": "absolute",
#         "cornerRadius": "14px",
#         "offsetTop": "14px",
#         "offsetStart": "14px",
#         "height": "26px",
#         "width": width,
#         "backgroundColor": bg
#     }

# # ============
# # Flex Card (作品集 carousel)
# # ============
# def build_portfolio_carousel():
#     return {
#         "type": "flex",
#         "altText": "Sui｜專案作品集",
#         "contents": {
#             "type": "carousel",
#             "contents": [
#                 # 作品 1：心理諮商地圖 Demo
#                 {
#                     "type": "bubble",
#                     "size": "kilo",
#                     ## Hero（封面圖）
#                     "hero": {
#                         "type": "image",
#                         "url": "https://i.imgur.com/j8AfACY.jpeg",
#                         "size": "full", #full 
#                         "aspectRatio": "20:13", #20:13
#                         "aspectMode": "cover", # cover
#                     },
#                     ## Title + 描述
#                     "body": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {"type": "text", "text": "心理諮商地圖 Demo", "weight": "bold", "size": "lg"},
#                             {
#                                 "type": "text",
#                                 "text": "Next.js + Leaflet + Redis Queue\n全台 614 間合作心理諮商診所地圖",
#                                 "size": "sm",
#                                 "wrap": True,
#                                 "margin": "md"
#                             },
#                             build_role_badge("前端 Next.js", "#111827")
#                         ]
#                     },
#                     ## 透過 message → "心理諮商地圖"
#                     ## 作品 → 一鍵 Demo
#                     ## 使用者看到 → 點按 → 立即體驗
#                     "footer": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {
#                                 "type": "button",
#                                 "action": {"type": "message", "label": "查看 Demo", "text": "心理諮商地圖"}
#                             }
#                         ]
#                     }
#                 },
#                 # 作品 2：地政自動化查詢 Demo
#                 {
#                     "type": "bubble",
#                     "size": "kilo",
#                     ## Hero
#                     "hero": {
#                         "type": "image",
#                         "url": "https://i.imgur.com/IZkcxQq.jpeg",
#                         "size": "full",
#                         "aspectRatio": "20:13",
#                         "aspectMode": "cover",
#                     },
#                     ## Title
#                     "body": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {"type": "text", "text": "地政自動化查詢", "weight": "bold", "size": "lg"},
#                             {
#                                 "type": "text",
#                                 "text": "Playwright + Cloud Run\n自動查詢段名地號，擷取謄本與地籍圖",
#                                 "size": "sm",
#                                 "wrap": True,
#                                 "margin": "md"
#                             }
#                         ]
#                     },
#                     #Demo 按鈕
#                     "footer": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {
#                                 "type": "button",
#                                 "action": {"type": "message", "label": "查看 Demo", "text": "地政查詢"}
#                             }
#                         ]
#                     }
#                 },
#                   # 作品 3：Everforest 活動票務系統（Backend）
#                 {
#                     "type": "bubble",
#                     "size": "kilo",
#                     ## Hero
#                     "hero": {
#                         "type": "image",
#                         "url": "https://i.imgur.com/L9uCggH.jpeg",  # 先沿用，之後再換成露營圖
#                         "size": "full",
#                         "aspectRatio": "20:13",
#                         "aspectMode": "cover",
#                     },
#                     ## Title 描述
#                     "body": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {"type": "text", "text": "Everforest 活動票務系統（Backend）", "weight": "bold", "size": "lg"},
#                             {
#                                 "type": "text",
#                                 "text": "Node.js + Express + PostgreSQL\n活動管理、購票下單、額滿控制、訂單通知",
#                                 "size": "sm",
#                                 "wrap": True,
#                                 "margin": "md"
#                             },
#                             {
#                                 "type": "text",
#                                 "text": "Tech：TypeORM｜JWT (HttpOnly Cookie)｜Docker｜Swagger",
#                                 "size": "xs",
#                                 "wrap": True,
#                                 "color": "#666666",
#                                 "margin": "md"
#                             }
#                         ]
#                     },
#                     "footer": {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "contents": [
#                             {
#                                 "type": "button",
#                                 "action": {"type": "message", "label": "查看 Demo", "text": "露營票務系統"}
#                             }
#                         ]
#                     }
#                 }

#             ]
#         }
#     }