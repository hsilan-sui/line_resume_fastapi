# app/utils/fuzzy.py
# 模糊比對clinics資料中的診所名稱
from difflib import SequenceMatcher
from app.data.clinic_loader import clinics
# ============
# fuzzy_match()
# ============
# 對使用者輸入的關鍵字（例如「心寧」、「大安診所」）做 模糊搜尋
# → 回傳最接近的診所前 5 筆
# 即使使用者輸入不完整、拼錯字、少兩三個字，你也能找到合理的診所
# ============
def fuzzy_match(keyword: str):
    results = []
    for c in clinics:
        # 逐筆比對診所名稱與 keyword =>ratio() 會回傳 0～1 之間的相似度 
        score = SequenceMatcher(None, c["org_name"], keyword).ratio()
        
        # 把相似度高於 0.55 的加入 results
        if score > 0.55:  # 你可以調整
            results.append((score, c))

    # 依相似度排序（高 → 低） 分數高 → 排第一
    results.sort(reverse=True, key=lambda x: x[0])

    # 只取前五名
    return [c for _, c in results][:5]