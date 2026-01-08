from app.line.flex_builder.main_menu import build_main_menu_flex
from app.line.quickbtn.main_quickreply import build_portfolio_quickreply

def build_home_entry_messages():
    welcome_text = (
        "您好，我是方箏 | Sui 👋\n"
        "這支 LINE OA 是我打造的互動作品集入口，您可以用 30 秒體驗 Demo。\n\n"
        "🌟 建議先玩：30 秒快速體驗\n"
        "1) 地政圖資自動查詢\n"
        "2) 免費諮商資源查找（傳送定位）\n"
        "👇 點下方選單開始"
    )

    # 文字訊息掛 quickReply 最穩（Flex 有時會 400）
    entry_text = {
        "type": "text",
        "text": welcome_text,
        "quickReply": build_portfolio_quickreply()
    }

    return [
        entry_text,
        build_main_menu_flex(),
    ]