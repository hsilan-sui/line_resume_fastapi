# # app/line/flex_builder/counseling.py

# app/line/flex_builder/counseling.py
from app.line.quickbtn.counseling_quickreply import build_counseling_quickreply

MOHW_URL = "https://www.mohw.gov.tw/cp-16-79408-1.html"
MAP_URL = "https://counseling-map.vercel.app/"

def build_counseling_entry():
    return {
        "type": "flex",
        "altText": "心理諮商｜免費專案查詢",
        "quickReply": build_counseling_quickreply(),  # ✅ 跟地政一樣：掛在 message 同層
        "contents": {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {"type": "text", "text": "心理諮商｜免費專案查詢", "weight": "bold", "size": "xl", "wrap": True},
                     # ✅ 醒目提醒框：引導先按 quickReply 的「傳送定位」
                    {
                        "type": "box",
                        "layout": "vertical",
                        "paddingAll": "12px",
                        "backgroundColor": "#ECFDF5",
                        "cornerRadius": "12px",
                        "spacing": "xs",
                        "contents": [
                            {"type": "text", "text": "💞 下一步", "size": "sm", "weight": "bold", "color": "#065F46"},
                            {"type": "text", "text": "請直接點擊左下方 傳送定位", "size": "md", "weight": "bold", "wrap": True, "color": "#047857"},
                            {"type": "text", "text": "只要分享大致位置即可查詢", "size": "sm", "wrap": True, "color": "#047857"},
                        ],
                    },
                    {"type": "text", "text": "15–45 歲心理健康支持方案｜每人最多 3 次（限個別諮商）", "size": "sm", "color": "#666666", "wrap": True},
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "margin": "md",
                        "contents": [
                            {"type": "text", "text": "🪪 首次到場：身分證或健保卡", "size": "sm", "wrap": True},
                            {"type": "separator", "margin": "md"},
                            {"type": "text", "text": "📍 使用方式 3 步", "weight": "bold", "size": "sm", "margin": "md"},
                            {
                                "type": "text",
                                "text": "1️⃣ 點下方 傳送定位 分享想查找的位置\n"
                                        "2️⃣ LINE會回傳該位置 最近 12 家合作機構 並標示免費配額狀態\n"
                                        "3️⃣ 點卡片可一鍵撥號 開網站 開地圖",
                                "size": "sm",
                                "wrap": True,
                                "color": "#555555"
                            },
                            {"type": "separator", "margin": "md"},
                            {"type": "text", "text": "🌿 或點擊⬇️公益網站版地圖：我有做網頁版整合各縣市公告名單，讓你更快找到可預約的合作機構", "size": "sm", "wrap": True, "color": "#555555"},
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
            "color": "#3B82F6",
            "height": "sm",
            "action": {"type": "uri", "label": "🖥️ 公益網站版地圖", "uri": MAP_URL}
        },
        {
            "type": "button",
            "style": "primary",
            "color": "#3B82F6",
            "height": "sm",
            "action": {"type": "uri", "label": "📄 衛福部方案說明", "uri": MOHW_URL}
        }
    ]
}

            # "footer": {
            #     "type": "box",
            #     "layout": "vertical",
            #     "spacing": "sm",
            #     "contents": [
            #         {"type": "button", "style": "link", "action": {"type": "uri", "label": "開啟網頁版地圖", "uri": MAP_URL}},
            #         {"type": "button", "style": "link", "action": {"type": "uri", "label": "衛福部方案說明", "uri": MOHW_URL}},
            #     ]
            # }
        }
    }

def build_counseling_demo_messages():
    return build_counseling_entry()
# from app.line.quickbtn.counseling_quickreply import build_counseling_quickreply

# MOHW_URL = "https://www.mohw.gov.tw/cp-16-79408-1.html"
# MAP_URL = "https://counseling-map.vercel.app/"


# def build_counseling_entry():
#     """
#     Do what:
#       - Flex 只做「公告 + 操作指引 + 開地圖」
#       - 不在 Flex 上掛 location quickReply（避免 LINE 400）
#     How:
#       - 定位功能改由「文字訊息 + quickReply(location)」提供
#     Why:
#       - location action 被判定不能用在 flex message 時會出現 LINE 400
#       - Text message + quickReply(location) 是最穩的官方用法
#     """
#     return {
#         "type": "flex",
#         "altText": "心理諮商｜免費專案查詢",
#         "contents": {
#             "type": "bubble",
#             "size": "mega",
#             "body": {
#                 "type": "box",
#                 "layout": "vertical",
#                 "spacing": "md",
#                 "contents": [
#                     {
#                         "type": "text",
#                         "text": "心理諮商｜免費專案查詢",
#                         "weight": "bold",
#                         "size": "xl",
#                         "wrap": True
#                     },
#                     {
#                         "type": "text",
#                         "text": "15–45 歲心理健康支持方案｜每人最多 3 次（限個別諮商）",
#                         "size": "sm",
#                         "color": "#666666",
#                         "wrap": True
#                     },
#                     {
#                         "type": "box",
#                         "layout": "vertical",
#                         "spacing": "sm",
#                         "margin": "md",
#                         "contents": [
#                             {"type": "text", "text": "🪪 首次到場：身分證或健保卡", "size": "sm", "wrap": True},
#                             {"type": "separator", "margin": "md"},
#                             {"type": "text", "text": "📍 使用方式 3 步", "weight": "bold", "size": "sm", "margin": "md"},
#                             {
#                                 "type": "text",
#                                 "text": "1 點下方 傳送定位 送出大致位置\n"
#                                         "2 回傳該地區最近 12 家合作機構 並標示免費配額狀態\n"
#                                         "3 點卡片可一鍵撥號 開網站 開地圖",
#                                 "size": "sm",
#                                 "wrap": True,
#                                 "color": "#555555"
#                             },
#                             {"type": "separator", "margin": "md"},
#                             {
#                                 "type": "text",
#                                 "text": "🌿 公益工具：整合各縣市公告名單，讓你更快找到可預約的合作機構",
#                                 "size": "sm",
#                                 "wrap": True,
#                                 "color": "#555555"
#                             }
#                         ]
#                     }
#                 ]
#             },
#             "footer": {
#                 "type": "box",
#                 "layout": "vertical",
#                 "spacing": "sm",
#                 "contents": [
#                     {"type": "button", "style": "link", "action": {"type": "uri", "label": "開啟網頁版地圖", "uri": MAP_URL}},
#                     {"type": "button", "style": "link", "action": {"type": "uri", "label": "衛福部方案說明", "uri": MOHW_URL}},
#                 ]
#             }
#         }
#     }


# def build_counseling_quickreply_text():
#     """
#     Do what: 用文字訊息承載 location quickReply（最穩）
#     How: 回一則 text + quickReply(location/message)
#     Why: 避免 flex message 掛 location quickReply 觸發 LINE 400
#     """
#     msg = {
#         "type": "text",
#         "text": "📍 直接點下方 傳送定位 即可開始查詢："
#     }
#     # quickReply 從外部模組引入，集中管理
#     msg.update(build_counseling_quickreply())
#     return msg


# def build_counseling_demo_messages():
#     """
#     Do what: Demo 入口回 2 則：先 quickReply text（可立刻按定位）再 flex 公告
#     Why: 既保留公告卡，又確保定位按鈕永遠可用
#     """
#     return [
#         build_counseling_entry(),
#         build_counseling_quickreply_text()
#     ]
