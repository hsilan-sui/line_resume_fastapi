# app/line/quickbtn/main_quickreply.py

def build_portfolio_quickreply():
    """
    Do what: 作品集導覽 quickReply（逛完作品後可繼續操作）
    How: 回 quickReply items（message 為主）
    Why: 降低 HR 操作成本，不用回主選單也能接著點
    """
    return {
        "items": [
            {"type": "action", "action": {"type": "message", "label": "🏡 地政查詢", "text": "地政"}},
            {"type": "action", "action": {"type": "message", "label": "🧠 諮商資源查找", "text": "心理諮商資源查找"}},

            {"type": "action", "action": {"type": "message", "label": "📇 LINE名片", "text": "LINE名片"}},

            {"type": "action", "action": {"type": "message", "label": "💻 GitHub", "text": "GitHub"}},
            {"type": "action", "action": {"type": "message", "label": "⬅️ 主選單", "text": "menu"}},
        ]
    }
