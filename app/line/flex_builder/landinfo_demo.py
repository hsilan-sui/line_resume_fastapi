# app/line/flex_builder/landinfo_demo.py
from urllib.parse import quote

def build_landinfo_demo_flex(base_url: str):
    """
    建立『地政 Demo』最小 Flex 卡片
    - 查段名 → 段號
    - 示意地號資料（mock）
    base_url: 你的 FastAPI 網域，例如 https://xxx.ngrok-free.app
    """

    name = quote("大利段")

    return {
        "type": "flex",
        "altText": "地政 Demo",
        "contents": {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "md",
                "contents": [
                    {
                        "type": "text",
                        "text": "地政圖資 Demo",
                        "weight": "bold",
                        "size": "lg"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "action": {
                            "type": "uri",
                            "label": "查段名 → 段號",
                            "uri": f"{base_url}/landinfo/section?name={name}"
                        }
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "action": {
                            "type": "uri",
                            "label": "示意地號資料",
                            "uri": f"{base_url}/landinfo/sample"
                        }
                    }
                ]
            }
        }
    }