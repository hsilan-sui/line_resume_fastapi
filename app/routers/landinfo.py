# app/routers/landinfo.py

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
import os
import requests

router = APIRouter()

# ----------------------
# 假資料：之後可以換成 JSON 檔
# ----------------------

# 你 Node 微服務的位址（先用 env，沒有就用預設）
NODE_LANDINFO_URL = os.getenv("NODE_LANDINFO_URL", "http://127.0.0.1:3001")

SECTION_DATA = {
    "大利段": [1938, 1941, 1982, 2018],
    "四稜段": [1123, 1128, 1130],
}

class LandinfoRequest(BaseModel):
    city: str           # "H"
    district: str       # "13" (townCode)
    sectionId: str | None = None  # 可選
    section: str | None = None    # 可選：段名
    landNo: str         # "1306"

# ---------------------------------------------------
# 1) GET /landinfo/section?name=大利段
#    功能：輸入段名，回傳對應的段號清單
# ---------------------------------------------------
@router.get("/landinfo/section")
def get_section_codes(name: str = Query(..., description="段名，例如：新光段")):
    codes = SECTION_DATA.get(name)
    if not codes:
        # 查不到也不要報錯，就回傳空陣列
        return {
            "section": name,
            "codes": [],
            "message": "查無此段名，請確認輸入是否正確"
        }

    return {
        "section": name,
        "codes": codes
    }

# ---------------------------------------------------
# 2) GET /landinfo/sample
#    功能：回傳一筆示意的地號資料（mock）
# ---------------------------------------------------
@router.get("/landinfo/sample")
def get_sample_landinfo():
    return {
        "section": "新光段",
        "land_no": "1949",
        "area": "312 m²",
        "owner": "（示意資料）",
        "screenshot": "https://example.com/mock.png"
    }


# ---------------------------------------------------
# 3) GET /landinfo/search
#    功能：搜尋段名 API（/landinfo/search）
# ---------------------------------------------------
@router.get("/landinfo/search")
def search_section(keyword: str = Query(..., description="關鍵字，例如：利 或 稜")):
    """
    Do What:
      用關鍵字搜尋段名（例如輸入「利」會找到「大利段」）

    How:
      在 SECTION_DATA 的 key（段名）裡做包含搜尋 (keyword in name)

    Why:
      之後前端可以先讓使用者輸入關鍵字 → 列出候選段名清單
    """

    # # name = 每個段名，例如 "大利段"、"四稜段"
    matches = [name for name in SECTION_DATA.keys() if keyword in name]

    return {
        "keyword": keyword,
        "matches": matches
    }


# ---------------------------------------------------
# 4) GET /landinfo/detail-mock
#    功能：新增 地號詳細資料
#.   回傳「一筆詳細地籍資料（用假資料）」
# ---------------------------------------------------
@router.get("/landinfo/detail-mock")
def get_land_detail(
    section: str = Query(..., description="段名，例如：大利段"),
    no: int = Query(..., description="地號，例如：1938")
):
    """
    Do What:
      根據「段名 + 地號」回傳一筆 mock 詳細地籍資料。
      未連接真實資料前，用假資料即可展示流程。

    Why:
      這支 API 是 我到時候要把原來的node 程式碼接過來做，因為playwright
      已經寫好了 自動化 / 地籍便民查詢截圖的基礎
    """

    # --- 模擬查詢：先看這個段名是不是存在 ---
    if section not in SECTION_DATA:
        return {
            "section": section,
            "no": no,
            "message": "查無此段名（mock）"
        }

    # --- 模擬：看這個地號是否在段名底下 ---
    if no not in SECTION_DATA[section]:
        return {
            "section": section,
            "no": no,
            "message": "查無此地號（mock）"
        }

    # --- 假資料：等未來接 Playwright 時再改成真實 ---
    detail = {
        "section": section,
        "land_no": no,
        "area": "312 m²",
        "usage": "農業用地",
        "zone": "山坡地保育區",
        "owner": "（示意資料）",
        "screenshot": "https://example.com/mock.png"
    }

    return detail

# ---------------------------------------------------
# 5) POST /landinfo/search
#    功能：新增 地號詳細資料
#.   回傳「一筆詳細地籍資料（用假資料）」
# ---------------------------------------------------
@router.post("/landinfo/detail")
def landinfo_detail(payload: LandinfoRequest):
    """
    Do what:
      FastAPI 代替 Postman，轉呼叫 Node /scrape 拿結果回傳

    How:
      requests.post(NODE_LANDINFO_URL + "/scrape", json=payload)

    Why:
      讓 LINE Bot 只打 FastAPI，不直接碰 Node
    """

    if not payload.sectionId and not payload.section:
        raise HTTPException(status_code=400, detail="sectionId or section is required")

    url = f"{NODE_LANDINFO_URL}/scrape"

    try:
        resp = requests.post(
            url,
            json=payload.model_dump(),
            timeout=120,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Failed to call Node service: {e}")

    # ✅ 這行超重要：Node 回錯就直接把 body 吐回來給你看
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Node service returned error",
                "node_url": url,
                "status_code": resp.status_code,
                "text": resp.text[:2000],
            },
        )

    # ✅ 如果 Node 回來不是 JSON，這裡會炸 -> 我們也讓它變可讀
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Node returned non-JSON response",
                "node_url": url,
                "status_code": resp.status_code,
                "text": resp.text[:2000],
            },
        )