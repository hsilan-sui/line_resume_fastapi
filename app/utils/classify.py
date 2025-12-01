# app/utils/classify.py
from app.utils.fuzzy import fuzzy_match #用到模糊比對

# ============
# classify_input() 
# LINE 使用者輸入會非常多樣，先自動判斷輸入類型 → 用正確查詢方式處理
# 依照使用者輸入的文字，判斷使用者「想查什麼類型」
# ============
# ① 判斷是否為「行政區」
# 把使用者輸入的文字（地址、地名）轉成 (緯度, 經度)
# 使用者可以輸入「地址」、「診所名稱」
# → 你需要把這些文字轉成座標
# → 才能用 haversine 算誰最近
# ============
def classify_input(text: str):
    # ① 判斷是否為「行政區」=> 只要包含區、鄉、鎮、市，就判為區域搜尋
    if any(k in text for k in ["區", "鄉", "鎮", "市"]):
        return "district"
    
    # ② 判斷是否為「地址」長安東路一段 12 號 => 多半是具體地址
    if any(k in text for k in ["路", "街", "大道", "巷", "號"]):
        return "address"
    
    # ③ 用 fuzzy search 判斷是否像診所名稱
    top = fuzzy_match(text)
    if top:
        return "clinic_keyword"

    # ④ 以上都不是 → 當作一般地名
    return "place"