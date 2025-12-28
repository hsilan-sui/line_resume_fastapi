# app/line/flex_builder/clinic_list.py

## 讓使用者立馬看到最快的資源：「目前可以預約的診所」
## 讓查詢體驗更快、更有效率
# 打造完整的 LINE OA 心理諮商查询 UX：
# - 一鍵導航
# - 一鍵撥打電話
# - 一鍵看官網
# - 滑動瀏覽 12 家診所
# - 回到作品集
# - 前往地圖網站
# - UX 設計和資料處理直觀

from app.line.flex_builder.clinic_item import build_clinic_flex_item # 引入單張診所卡片


# ============
# Flex Card (多診所 carousel)＝> 
# build_clinic_flex = 把很多名片裝進一本「診所名片本」（carousel）
# ============
def build_clinic_flex(results):
    '''
    將多筆診所 list → 變成 LINE Flex Carousel（最多 12 卡片）。
    並附上一組 Quick Reply，讓查詢 → Flex → 導回網站 或 作品集形成「完整使用路徑」：
    - 「看政府合作心理諮商地圖」
    - 「回到作品集」      
    '''

    # ① 生成 12 個 bubble(使用bubble 函式)
    ### 把 results（搜尋結果 list）
    ### 逐筆丟給 build_clinic_flex_item()
    ### 最後回傳一個「bubble list」
    bubbles = [build_clinic_flex_item(c) for c in results[:12]]

    # ② 包裝成 Flex Message
    return {
        "type": "flex",
        "altText": "心理諮商診所查詢結果", #LINE 無法顯示 flex 時使用
        "contents": {
            "type": "carousel", #真正展示內容 → carousel
            "contents": bubbles # 剛組的每張診所 bubble list
        },
    # ③ Quick Reply 設計 => 放了下方 UX 快捷按鈕
        # "quickReply": {
        #     "items": [
        #         ## Quick Reply 1：連到我做的全台心理諮商查詢網站＝>網站則是「完整資訊」
        #         {
        #             "type": "action",
        #             "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_34_article.png",
        #             "action": {
        #                 "type": "uri",
        #                 "label": "查找政府合作全台心理諮商網站",
        #                 "uri": "https://counseling-map.vercel.app/"
        #             }
        #         },
        #         ## Quick Reply 2：回到作品集 => 提供返回「作品集 Flex Menu」的入口(使用者不會迷路)
        #         {
        #             "type": "action",
        #             "imageUrl": "https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_17_bookmark.png",
        #             "action": {
        #                 "type": "message",
        #                 "label": "回到作品集",
        #                 "text": "作品集"
        #             }
        #         }
        #     ],
            
        # }
    }







# ============
# 過濾：只留下「有名額」的診所=> 因為LINE OA 是「互動入口」
# ============
def filter_available(clinic_list):
    return [c for c in clinic_list if c.get("has_quota") is True]