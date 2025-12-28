# ✅ 地政 quick reply（可加回主選單）
def build_landinfo_quickreply():
    return {
        "items": [
            {"type": "action", "action": {"type": "message", "label": "➡️ 直接跑範例", "text": "新光段 549"}},
            {"type": "action", "action": {"type": "message", "label": "🟢 回作品集", "text": "作品集"}},
            # {"type": "action", "action": {"type": "message", "label": "🟡 回主選單", "text": "menu"}},
        ]
    }
