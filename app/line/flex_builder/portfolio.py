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
                                "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/landinfo_03.png",
                                "後端 Node.js ",
                                "#FF4D8D"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "地政圖資 LINE 自動查詢", "weight": "bold", "size": "lg"},
                                    {
                                        "type": "separator",
                                        "margin": "md"
                                    },
                                    {"type": "text", "text": "📝 LINE輸入 ➜ 地段地號", "size": "sm", "wrap": True, "color": "#6B7280"},
                                    {"type": "text", "text": "🔍 系統先回 ➜ 已收到查詢", "size": "sm", "wrap": True, "color": "#6B7280"},
                                    {"type": "text", "text": "✅ 完成後 ➜ 推播 地圖與重點資料", "size": "sm", "wrap": True, "color": "#111827"},
                                
                                ]
                            }
                        ]
                    },
                    "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "paddingAll": "12px",
                    "contents": [   
                            {
                            "type": "button",
                            "style": "primary",
                            "color": "#14B8A6",
                            "height": "sm",
                            "action": {"type": "message", "label": "🚀 立即體驗", "text": "地政"}
                            }
                            # ,
                            # {
                            # "type": "button",
                            # "style": "secondary",
                            # "height": "sm",
                            # "action": {"type": "uri", "label": "💻 GitHub Repo", "uri": "https://github.com/hsilan-sui/landinfo_api"}
                            # }
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
                                "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/com_sideproject.png",
                                "前端 Next.js",
                                "#01B468"
                            ),
                            {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "paddingAll": "16px",
                            "contents": [
                                {"type": "text", "text": "免費諮商資源LINE一鍵查", "weight": "bold", "size": "lg"},
                                {"type": "separator", "margin": "md"},
                                
                                {"type": "text", "text": "📍 定位查詢 ➜ 回傳最近12家診所", "size": "sm", "wrap": True, "color": "#6B7280"},
                                {"type": "text", "text": "✅ 免費配額 ➜ 衛福部專案免費三次", "size": "sm", "wrap": True, "color": "#6B7280"},
                                {"type": "text", "text": "☎️ 診所卡片 ➜ 一鍵撥號 與 導航", "size": "sm", "wrap": True, "color": "#111827"},
                                {"type": "text", "text": "或網頁版地圖查找(自架公益網站)", "size": "sm", "wrap": True, "color": "#6B7280"},

                                {"type": "text", "text": "備註 位置可模糊傳送也能查", "size": "xs", "wrap": True, "color": "#9CA3AF"}
  ]
                        }
                    ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "paddingAll": "12px",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#14B8A6",
                                    "height": "sm",
                                    "action": {"type": "message", "label": "🚀 立即體驗", "text": "心理諮商資源查找"}
                                }
                            ]
                        }
                    },
                # 作品 3：Everforest 活動票務系統（改成作品1同款）
                    {
                        "type": "bubble",
                        "size": "kilo",
                        "body": {
                            "type": "box",
                            "layout": "vertical",
                            "paddingAll": "0px",
                            "contents": [
                                build_image_header(
                                    "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/everforest.png",
                                    "後端 Node.js",
                                    "#FF4D8D"
                                ),
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "sm",
                                    "paddingAll": "16px",
                                    "contents": [ 
                                        {"type": "text", "text": "露營活動票務系統", "weight": "bold", "size": "lg"},
                                        {"type": "separator", "margin": "md"},

                                        {"type": "text", "text": "🧾 活動管理 ➜ 活動建立｜上架流程", "size": "sm", "wrap": True, "color": "#6B7280"},
                                        {"type": "text", "text": "🎟 報名流程 ➜ 方案選擇", "size": "sm", "wrap": True, "color": "#6B7280"},
                                        {"type": "text", "text": "🛒 購票下單 ➜ 建立訂單｜付款狀態管理", "size": "sm", "wrap": True, "color": "#6B7280"},
                                        {"type": "text", "text": "✉️ 通知系統 ➜ 訂單成功信｜電子票券信", "size": "sm", "wrap": True, "color": "#6B7280"},
                                        {"type": "text", "text": "🤖 AI 審查 ➜ 活動上架前檢查：敏感詞｜法規風險｜圖片內容", "size": "sm", "wrap": True, "color": "#6B7280"}

                                    ]
                                }
                            ]
                        },
                        "footer": {
                            "type": "box",
                            "layout": "vertical",
                            "spacing": "sm",
                            "paddingAll": "12px",
                            "contents": [
                                {
                                    "type": "button",
                                    "style": "primary",
                                    "color": "#14B8A6",
                                    "height": "sm",
                                    "action": {
                                    "type": "uri",
                                    "label": "🚀 立即體驗",
                                    "uri": "https://camping-project-one.vercel.app/"
                                    }
                                },                  
                                {
                                "type": "button",
                                "style": "secondary",
                                "height": "sm",
                                "action": {
                                    "type": "uri",
                                    "label": "📂 查看 GitHub",
                                    "uri": "https://github.com/hsilan-sui/everforest-backend"
                                }}
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
                                "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/line_bot_img.png",  # 換成你的截圖或 UI 圖
                                "後端 FastAPI",
                                "#FF4D8D"
                            ),
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "paddingAll": "16px",
                                "contents": [
                                    {"type": "text", "text": "LINE Bot 互動作品集", "weight": "bold", "size": "lg"},
                                    {"type": "separator", "margin": "md"},

                                    {"type": "text", "text": "👋 加入好友 ➜ 自動回歡迎與導覽", "size": "sm", "wrap": True, "color": "#6B7280"},
                                    {"type": "text", "text": "🧩 主選單入口 ➜ 作品卡與指令流程", "size": "sm", "wrap": True, "color": "#6B7280"},
                                    {"type": "text", "text": "🚀 串接 Demo ➜ 導到地政與地圖功能", "size": "sm", "wrap": True, "color": "#111827"},
                                ]
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "paddingAll": "12px",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "color": "#14B8A6",
                                "height": "sm",
                                "action": {"type": "message", "label": "🚀 立即體驗", "text": "welcomeMsg"}
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