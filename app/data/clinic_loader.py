# app/data/clinic_loader.py
import json
# ============
# 載入診所資料
# ============
with open("data/clinic.json", "r") as f:
    data = json.load(f)

# ➤ 你的 JSON = 外層 list → 取第一筆 → rows
if isinstance(data, list) and len(data) > 0 and "rows" in data[0]:
    clinics = data[0]["rows"]
else:
    raise ValueError("clinic.json 格式不符合預期")
