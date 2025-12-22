# app/handlers/landinfo_chat.py
import os
import re
import requests
import redis.asyncio as redis

from app.line.client import reply_message

def build_landinfo_quickreply():
    return {
        "items": [
            {"type": "action", "action": {"type": "message", "label": "直接跑範例", "text": "大利段 1306"}},
            {"type": "action", "action": {"type": "message", "label": "回作品集", "text": "作品集"}},
            {"type": "action", "action": {"type": "message", "label": "回主選單", "text": "menu"}},
        ]
    }

NODE_LANDINFO_URL = os.getenv("NODE_LANDINFO_URL", "http://127.0.0.1:3001").rstrip("/")
NODE_JOB_TOKEN = os.getenv("NODE_JOB_TOKEN")
REDIS_URL = os.getenv("REDIS_URL", "")
MODE_TTL = int(os.getenv("LANDINFO_MODE_TTL_SEC", "600"))  # 預設 10 分鐘



# ✅ Redis client（TLS：rediss://...）
rds = redis.from_url(REDIS_URL, decode_responses=True) if REDIS_URL else None

def enqueue_land_job(payload: dict):
    url = f"{NODE_LANDINFO_URL}/jobs"
    resp = requests.post(
        url,
        json=payload,
        headers={"x-job-token": NODE_JOB_TOKEN},
        timeout=15,
    )
    return resp

def _mode_key(user_id: str) -> str:
    return f"mode:landinfo:{user_id}"

def _parse_section_landno(text: str):
    """
    Do what: 解析「大利段 1306」或「大利段1306-0000」
    How: regex 分段名 + 地號主號 + optional 子號
    Why: 先做最穩定的純文字 MVP
    """
    msg = text.strip().replace("\u200b", "").replace("\n", "")
    m = re.match(r"^(.+?段)\s*([0-9]{1,4})(?:\s*[-－–—~～]\s*([0-9]{1,4}))?$", msg)
    if not m:
        return None
    section = m.group(1).strip()
    no1 = m.group(2)
    no2 = (m.group(3) or "").strip()
    land_no = f"{no1}-{no2}" if no2 else no1
    return section, land_no

async def _enter_mode(user_id: str):
    if not rds:
        return
    await rds.set(_mode_key(user_id), "1", ex=MODE_TTL)  # ✅ TTL

async def _exit_mode(user_id: str):
    if not rds:
        return
    await rds.delete(_mode_key(user_id))

async def _in_mode(user_id: str) -> bool:
    if not rds:
        return False
    v = await rds.get(_mode_key(user_id))
    return v == "1"

async def handle_landinfo_chat(event: dict, reply_token: str, msg: str) -> bool:
    """
    True  = 已處理（webhook 直接 return）
    False = 不關地政，讓 webhook 繼續跑原本流程
    """
    
    user_id = (event.get("source") or {}).get("userId")
    if not user_id:
        return False
    
    print(f"[地政聊天] 收到訊息：{msg}")
    print(f"[地政聊天] 使用者 ID：{user_id}")

    # 0) 支援取消
    if msg in ("取消", "退出", "離開"):
        if await _in_mode(user_id):
            await _exit_mode(user_id)
            reply_message(reply_token, [{"type": "text", "text": "已離開地政模式 ✅"}])
            return True
        return False

    # 1) 入口：打「地政」
    if msg == "地政":
        await _enter_mode(user_id)
        reply_message(reply_token, [{
            "type": "text",
            "text": "✅ 地政圖資查詢（目前固定：桃園市／復興區）\n請輸入：大利段 1306（或 1306-0000）\n離開請輸入：取消"
        }])
        return True

    # 2) 不是地政模式 → 放行
    # if not await _in_mode(user_id):
    #     return False
    # 2) 判斷是否為合法地號格式（大利段1306）
    parsed = _parse_section_landno(msg)
    if parsed:
        await _enter_mode(user_id)  # 可選，順便讓它進 mode（未來可保留前後文）
    else:
        # 如果不是地號格式，也沒進入 mode → 放行
        if not await _in_mode(user_id):
            return False

        # 格式不對，但在 mode 裡 → 提示正確格式
        await _enter_mode(user_id)
        reply_message(reply_token, [{
            "type": "text",
            "text": "格式不對喔，請輸入：大利段 1306（或 大利段 1306-0000）\n離開請輸入：取消"
        }])
        return True

    # 3) 成功解析：開始派工
    section, land_no = parsed

    # enqueue 到 Node /jobs（worker 會 push 結果）
    try:
        if not NODE_JOB_TOKEN:
            reply_message(reply_token, [{
                "type": "text",
                "text": "⚠️ 系統未設定 NODE_JOB_TOKEN，請檢查 FastAPI .env 並重啟服務"
            }])
            return True

        payload = {
            "city": "H",        # 桃園市
            "district": "13",   # 復興區 townCode
            "section": section,
            "landNo": land_no,
            "userId": user_id,
        }

        resp = enqueue_land_job(payload)  # ✅ 會帶 x-job-token

        if resp.status_code != 200:
            reply_message(reply_token, [{
                "type": "text",
                "text": f"⚠️ 入列失敗：{resp.status_code}\n{resp.text[:300]}"
            }])
            return True
    except Exception as e:
        reply_message(reply_token, [{
            "type": "text",
            "text": f"⚠️ 連不到 Node 派工服務（/jobs）：{e}"
        }])
        return True

    # 4) 提示成功，離開地政模式
    await _exit_mode(user_id)
    
    reply_message(reply_token, [{
        "type": "text",
        "text": f"🔍 已收到查詢：【桃園市 復興區 {section} {land_no}】\n約 30~60 秒會推播結果 ✅",
        "quickReply": build_landinfo_quickreply()
    }])
    return True
