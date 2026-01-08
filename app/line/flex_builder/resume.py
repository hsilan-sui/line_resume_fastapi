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
        "altText": "Sui｜互動式履歷首頁",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [

                    # ======================
                    # 1) Hero Image（全版背景）
                    # ======================
                    {
                        "type": "image",
                        "url": "https://pub-1e15d55216a149c193d07024bf1d5269.r2.dev/screenshots/fangchengyu.jpg",
                        "size": "full",
                        "aspectMode": "cover",
                        "aspectRatio": "2:3",
                        "gravity": "top"
                    },

                    # ======================
                    # 2) Overlay 資訊卡（底部黑透明）
                    # ======================
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [

                            # --- 個人定位職稱 ---
                            {
                                "type": "text",
                                "text": "後端工程師 Backend Engineer",
                                "size": "md",
                                "color": "#ffffff",
                                "weight": "bold",
                                "wrap": True
                            },

                            # --- 技能快速摘要 ---
                            {
                                "type": "text",
                                "text": "Node.js · FastAPI · Automation · LINE BOT · AI-API串接",
                                "color": "#ffffffcc",
                                "size": "sm",
                                "wrap": True,
                                "margin": "md"
                            },
                            # --- 技能能力指標（icon + 標籤） ---
                            {
                                "type": "box",
                                "layout": "vertical",
                                "spacing": "sm",
                                "margin": "md",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {"type": "icon", "url": "https://developers-resource.landpress.line.me/fx/img/restaurant_regular_32.png"},
                                            {
                                                "type": "text",
                                                "text": "後端系統整合與資料流設計",
                                                "weight": "bold",
                                                "margin": "sm",
                                                "flex": 0,
                                                "color": "#ffffff"
                                            },
                                            {
                                                "type": "text",
                                                "text": "專長",
                                                "size": "sm",
                                                "align": "end",
                                                "color": "#ffffff80"
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {"type": "icon", "url": "https://developers-resource.landpress.line.me/fx/img/restaurant_large_32.png"},
                                            {
                                                "type": "text",
                                                "text": "後端服務實作與自動化流程",
                                                "weight": "bold",
                                                "margin": "sm",
                                                "flex": 0,
                                                "color": "#ffffff"
                                            },
                                            {
                                                "type": "text",
                                                "text": "主力",
                                                "size": "sm",
                                                "align": "end",
                                                "color": "#ffffff80"
                                            }
                                        ]
                                    }
                                ]
                            },
                            # --- CTA（查看作品集） ---
                            # {
                            #     "type": "box",
                            #     "layout": "vertical",
                            #     "contents": [
                            #         {"type": "filler"},
                            #         {
                            #             "type": "box",
                            #             "layout": "baseline",
                            #             "contents": [
                            #                 {"type": "filler"},
                            #                 {
                            #                     "type": "text",
                            #                     "text": "查看作品集",
                            #                     "color": "#ffffff",
                            #                     "flex": 0,
                            #                     "size": "sm"
                            #                 },
                            #                 {"type": "filler"}
                            #             ],
                            #             "spacing": "sm"
                            #         },
                            #         {"type": "filler"}
                            #     ],
                            #     "borderWidth": "1px",
                            #     "cornerRadius": "4px",
                            #     "spacing": "sm",
                            #     "borderColor": "#ffffff",
                            #     "margin": "xxl",
                            #     "height": "40px",
                            #     "action": {
                            #         "type": "message",
                            #         "text": "作品集"
                            #     }
                            # }
                        ],
                        "position": "absolute",
                        "offsetBottom": "0px",
                        "offsetStart": "0px",
                        "offsetEnd": "0px",
                        "backgroundColor": "#000000B3",
                        "paddingAll": "20px"
                    },

                   # ======================
                    # 3) 左上角品牌 Badge（姓名）
                    # ======================
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "游方箏 | Sui",
                                "align": "center",
                                "size": "xs",
                                "color": "#FBFBFF"
                            }
                        ],
                        "position": "absolute",
                        "cornerRadius": "20px",
                        "offsetTop": "18px",
                        "backgroundColor": "#01B468",
                        "offsetStart": "18px",

                        # 用 padding 讓高度自然撐開，比 height 好控制
                        "paddingAll": "4px",

                        # 可以留著 width，讓膠囊寬度固定
                        "width": "96px",

                        # 垂直置中（雖然只有一個 text，但加了比較保險）
                        "justifyContent": "center",
                        "alignItems": "center"
                    }
                ],
                "paddingAll": "0px"
            },
            # 點線
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [

                    {
                    "type": "text",
                    "text": "工作經歷 Timeline",
                    "color": "#b7b7b7",
                    "size": "xs"
                    },

                    {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                        "type": "text",
                        "text": "2024.11–2025.05",
                        "size": "xs",
                        "gravity": "center",
                        "color": "#666666",
                        "flex": 2,
                        "wrap": True,
                        
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            { "type": "filler" },
                            {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "cornerRadius": "30px",
                            "height": "12px",
                            "width": "12px",
                            "borderColor": "#EF454D",
                            "borderWidth": "2px"
                            },
                            { "type": "filler" }
                        ],
                        "flex": 0
                        },
                        {
                        "type": "text",
                        "text": "擎天有限公司｜後端工程師",
                        "gravity": "center",
                        "flex": 5,
                        "size": "sm",
                        "wrap": True,
                        "color": "#b7b7b7"
                        }
                    ],
                    "spacing": "lg",
                    "cornerRadius": "30px",
                    "margin": "xl"
                    },

                    {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [ { "type": "filler" } ],
                        "flex": 2
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                { "type": "filler" },
                                {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "2px",
                                "backgroundColor": "#B7B7B7"
                                },
                                { "type": "filler" }
                            ],
                            "flex": 1
                            }
                        ],
                        "width": "12px"
                        },
                        {
                        "type": "text",
                        "text": "MicroPython · IoT 裝置資料系統 · MQTT · OTA · API 整合",
                        "gravity": "center",
                        "flex": 5,
                        "size": "xs",
                        "color": "#8c8c8c",
                        "wrap": True
                        }
                    ],
                    "spacing": "lg",
                    "height": "64px"
                    },

                    {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                        "type": "text",
                        "text": "2025.06–至今",
                        "gravity": "center",
                        "size": "xs",
                        "color": "#666666",
                        "flex": 2,
                        "wrap": True
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            { "type": "filler" },
                            {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [],
                            "cornerRadius": "30px",
                            "width": "12px",
                            "height": "12px",
                            "borderWidth": "2px",
                            "borderColor": "#6486E3"
                            },
                            { "type": "filler" }
                        ],
                        "flex": 0
                        },
                        {
                        "type": "text",
                        "text": "接案｜後端系統與 AI 整合實作",
                        "gravity": "center",
                        "flex": 5,
                        "size": "sm",
                        "wrap": True,
                        "color": "#b7b7b7"
                        }
                    ],
                    "spacing": "lg",
                    "cornerRadius": "30px"
                    },

                    {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                        "type": "box",
                        "layout": "baseline",
                        "contents": [ { "type": "filler" } ],
                        "flex": 2
                        },
                        {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                { "type": "filler" },
                                {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [],
                                "width": "2px",
                                "backgroundColor": "#6486E3"
                                },
                                { "type": "filler" }
                            ],
                            "flex": 1
                            }
                        ],
                        "width": "12px"
                        },
                        {
                        "type": "text",
                        "text": "FastAPI · Automation · AI Agent · LINE BOT",
                        "gravity": "center",
                        "flex": 5,
                        "size": "xs",
                        "color": "#8c8c8c",
                        "wrap": True
                        }
                    ],
                    "spacing": "lg",
                    "height": "64px"
                    },
                    {
                    "type": "separator",
                    "margin": "xl"
                    },
                    {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "margin": "lg",
                    "contents": [
                        {
                        "type": "button",
                        "style": "primary",
                        "color": "#14B8A6",
                        "height": "sm",
                        "action": {
                            "type": "uri",
                            "label": "📄 游方箏履歷表",
                            "uri": "https://drive.google.com/file/d/1Pu2321lWagtWPOlhmKCY8qh0fLT9g0kO/view?usp=sharing"
                        }
                        }
                    ]
                    }
 
                ],
                "paddingAll": "12px",
                "spacing": "md"
                },
                

        }
    }
    return flex