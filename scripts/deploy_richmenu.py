# ./scripts/deploy_richmenu.py
#poetry run python scripts/deploy_richmenu.py
# do what?
# 用 httpx 打 LINE Messaging API：建立 rich menu、上傳圖片、設 default
# => Rich Menu 圖片 + 點擊熱區 上傳到 LINE，並設成全體使用者的預設 Rich Menu

# steps:
# 1) 建立 Rich Menu（先上傳熱區規格） → 拿到 richMenuId
# 2) 上傳圖片（把 PNG 綁到這個 richMenuId）
# 3) 設為預設（所有 user 都用這個 rich menu）

# how? 

import os
import httpx
from pathlib import Path
from dotenv import load_dotenv



HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent / ".env")  # 專案根目錄的 .env
DEFAULT_IMG = HERE / "assets" / "richmenu" / "sui_fastapi_richmenu.png"


# 0) 匯入 spec：把「圖尺寸 / 熱區 / 動作」抽離
from richmenu_home_spec import W, H, AREAS_PCT, ACTIONS

# 1) 讀取 Token
TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("Missing LINE_CHANNEL_ACCESS_TOKEN")

# 2) 兩個 API host：一般 API 跟 上傳圖片 用不同網域
API_BASE = "https://api.line.me" # LINE 的「建立 richmenu / 設預設」
API_DATA_BASE = "https://api-data.line.me" # LINE 的「上傳圖片 content」走 api-data.line.me


# 3) 比例轉像素：LINE 要的是整數像素 bounds => 把 AREAS_PCT 的 0~1 比例轉成像素
# LINE richmenu 的 bounds 格式只能吃像素整數
# 比例 × 圖寬或圖高
def pct_to_bounds(p, W: int, H: int):
    return {
        "x": round(p["x"] * W),
        "y": round(p["y"] * H),
        "width": round(p["w"] * W),
        "height": round(p["h"] * H),
    }

# 4) 組合 areas：每個熱區都要有 bounds + action
# 把 spec 轉成 LINE API 需要的 areas 陣列
# 避免「畫了熱區但忘了行為」——直接 raise 讓你部署前就知道錯
def build_areas():
    areas = []
    for key, rect in AREAS_PCT.items():
        if key not in ACTIONS:
            raise ValueError(f"Missing action for key: {key}")
        areas.append({
            "bounds": pct_to_bounds(rect, W, H),
            "action": ACTIONS[key],
        })
    return areas


# 5) 建立 richmenu payload：送到 LINE 建立物件
def build_richmenu_payload():
    # 這些欄位是 LINE Rich Menu object 的典型必填
    # size 要跟你的圖一致：2500x1686
    return {
        "size": {"width": W, "height": H}, # 一定要跟圖片一致（不一致會點歪）
        "selected": True, # 建立後預設選取（但要讓所有 user 生效還要第 3 步）
        "name": "home-menu", #給你後台辨識
        "chatBarText": "點我開啟主選單", #聊天室底下那條開啟選單的文字
        "areas": build_areas(), # 熱區清單（上一步組好的）
    }

# 6) Header：帶 Bearer token
def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"} #LINE Messaging API 用 Bearer token 認證


# 7) main：真正做「建立 → 上傳圖 → 設預設」
#用 async client 讓 HTTP 呼叫乾淨、也能擴充更多步驟
async def main(image_path: str):
    payload = build_richmenu_payload()

    async with httpx.AsyncClient(timeout=60) as client:
        # 1) Step 1 建立 rich menu（拿 richMenuId）
        # WHAT：把「熱區規格」先註冊到 LINE
        # WHY：必須先拿到 richMenuId，圖片才能綁上去
        # raise_for_status()：HTTP 不是 2xx 直接丟例外，讓你一看就知道失敗原因
        r = await client.post(
            f"{API_BASE}/v2/bot/richmenu",
            headers={**auth_headers(), "Content-Type": "application/json"},
            json=payload,
        )
        r.raise_for_status()
        rich_menu_id = r.json()["richMenuId"]

        # Step 2 上傳圖片（綁到 richMenuId）
        # 圖片上傳走 api-data host
        # WHAT：上傳 PNG bytes
        # WHY：這步做完，richmenu 才會真的顯示出你的圖
        # Content-Type: image/png：必須正確，否則 LINE 可能拒收
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        r2 = await client.post(
            f"{API_DATA_BASE}/v2/bot/richmenu/{rich_menu_id}/content",
            headers={**auth_headers(), "Content-Type": "image/png"},
            content=img_bytes,
        )
        r2.raise_for_status()

        # 3) Step 3 設成預設（所有 user 都看到）
        # WHAT：把這個 rich menu 設定為「所有使用者」的預設 rich menu
        # WHY：不做這步，你只是建好物件，但不一定會顯示在使用者端
        r3 = await client.post(
            f"{API_BASE}/v2/bot/user/all/richmenu/{rich_menu_id}",
            headers=auth_headers(),
        )
        r3.raise_for_status()

    print("OK default richMenuId =", rich_menu_id)

# 8) 入口：直接跑
if __name__ == "__main__":
    import asyncio
    # 匯出圖檔路徑
    asyncio.run(main(str(DEFAULT_IMG)))

