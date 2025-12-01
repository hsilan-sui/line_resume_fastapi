# app/utils/geo.py
# 使用者可以輸入「地址」、「診所名稱」
# → 把這些文字轉成座標 geocode()
# → 才能用 haversine 算誰最近 haversine()
import math
import requests

# ============
# geocode() — 地址 / 關鍵字 → 經緯度（lat, lon）
# ============
# 透過 OpenStreetMap 的 Nominatim API 做地理編碼（Geocoding）
# 把使用者輸入的文字（地址、地名）轉成 (緯度, 經度)
# 使用者可以輸入「地址」、「診所名稱」
# → 你需要把這些文字轉成座標
# → 才能用 haversine 算誰最近
# ============
def geocode(query: str):
    """
    將地址字串送到 OSM Nominatim API，取得 (lat, lon)
    回傳:
        (lat, lon)  或 None（查不到）
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }

    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
    except Exception as e:
        print("[Geocode Error]", e)
        return None

    data = r.json()

    # 查無資料
    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])

# ============
# haversine() — 計算地球上兩個經緯度之間的「球面距離」（公里）
# 使用者的定位點 → 最近的心理諮商診所
# Google Map、Uber、外送平台也用類似概念
# ============
def haversine(lat1, lon1, lat2, lon2):
    """
    計算地球上兩組經緯度的球面距離（公里）
    Haversine 公式：
    d = 2 * R * asin( sqrt(a) )
    """
    R = 6371  # 地球半徑（km）

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    # Haversine 公式 => 回傳公里數（R=6371km 是地球半徑）
    return 2 * R * math.asin(math.sqrt(a))

