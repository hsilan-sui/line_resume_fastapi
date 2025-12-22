# app/line/flex_builder/counseling.py

MOHW_URL = "https://www.mohw.gov.tw/cp-16-79408-1.html"
MAP_URL = "https://counseling-map.vercel.app/"


def build_counseling_entry():
    """
    Do what:
      - Flex 只做「公告 + 操作指引 + 開地圖」
      - 不在 Flex 上掛 location quickReply（避免 LINE 400）
    How:
      - 定位功能改由「文字訊息 + quickReply(location)」提供
    Why:
      - 你現在遇到的 400 就是 location action 被判定不能用在 flex message
      - Text message + quickReply(location) 是最穩的官方用法
    """
    return {
        "type": "flex",
        "altText": "心理支持方案｜免費名額查詢",
        "contents": {
            "type": "bubble",
            "size": "mega",
            "hero": {
                "type": "image",
                "url": "https://i.imgur.com/Zaa9d8R.jpeg",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "全台心理諮商診所免費配額查詢",
                        "weight": "bold",
                        "size": "xl",
                        "wrap": True
                    },
                    {
                        "type": "text",
                        "text": "15–45 歲心理健康支持方案｜每人最多 3 次（限個別諮商）",
                        "size": "sm",
                        "color": "#666666",
                        "wrap": True
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "🪪 首次到場：身分證或健保卡",
                                "size": "sm",
                                "wrap": True
                            },
                            {"type": "separator", "margin": "md"},
                            {
                                "type": "text",
                                "text": "📍 使用方式（3 步）",
                                "weight": "bold",
                                "size": "sm",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "1) 點下方「傳送定位」的送出大概位置\n"
                                        "2) 會回傳離您最近 12 家合作機構（優先顯示有免費配額的診所）\n"
                                        "3) 選一家用 電話／LINE／官網 預約，並說：「我要使用 15–45 方案」",
                                "size": "sm",
                                "wrap": True,
                                "color": "#555555"
                            },
                            {"type": "separator", "margin": "md"},
                            {
                                "type": "text",
                                "text": "🌿 公益工具：整合各縣市公告名單，讓你更快找到「可預約」的合作機構",
                                "size": "sm",
                                "wrap": True,
                                "color": "#555555"
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
                        "style": "link",
                        "action": {
                            "type": "uri",
                            "label": "開啟網站地圖",
                            "uri": MAP_URL
                        }
                    },
                    {
                        "type": "button",
                        "style": "link",
                        "action": {
                            "type": "uri",
                            "label": "衛福部方案說明",
                            "uri": MOHW_URL
                        }
                    }
                ]
            }
        }
    }


def build_counseling_quickreply_text():
    """
    Do what: 用「文字訊息」承載 location quickReply（最穩）
    How: 回一則 text + quickReply(location/message)
    Why: 避免 flex message 掛 location quickReply 觸發 LINE 400
    """
    return {
        "type": "text",
        "text": "📍 直接點下方 傳送定位 即可開始查詢：",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_24_location.png",
                    "action": {"type": "location", "label": "傳送我的定位"}
                },
                # {
                #     "type": "action",
                #     "action": {"type": "message", "label": "衛福部方案說明", "text": "衛福部方案說明"}
                # },
                {
                    "type": "action",
                    "action": {"type": "message", "label": "回作品集", "text": "作品集"}
                }
            ]
        }
    }


def build_counseling_demo_messages():
    """
    Do what: Demo 入口回 2 則：先 quickReply text（可立刻按定位）再 flex 公告
    Why: 既保留你要的公告卡，又確保定位按鈕永遠可用
    """
    return [
        build_counseling_entry(),
        build_counseling_quickreply_text()
    ]
