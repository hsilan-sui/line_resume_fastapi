# app/line/quickbtn/counseling_quickreply.py

def build_counseling_quickreply():
    return {
        "items": [
            {
                "type": "action",
                "action": {"type": "location", "label": "傳送定位"}
            },
            {
                "type": "action",
                "action": {"type": "message", "label": "🟢 回作品集", "text": "作品集"}
            }
        ]
    }
