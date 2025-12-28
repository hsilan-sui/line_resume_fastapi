# app/handlers/landinfo_chat.py
import os
import re
import requests
import redis.asyncio as redis

from app.line.client import reply_message
# 底部快速回覆鍵
from app.line.quickbtn.landinfo_quickreply import build_landinfo_quickreply

# =========
# ENV
# =========
NODE_LANDINFO_URL = os.getenv("NODE_LANDINFO_URL", "http://127.0.0.1:3001").rstrip("/")
NODE_JOB_TOKEN = os.getenv("NODE_JOB_TOKEN")
MODE_TTL = int(os.getenv("LANDINFO_MODE_TTL_SEC", "600"))  # 預設 10 分鐘


# =========
# Redis client (lazy init)
# 目的：避免 import 時就把 REDIS_URL 固定死（你換 .env 會遇到「還在連 Upstash」）
# =========
_REDIS_URL_CACHED = None
_RDS = None


def get_redis():
    """
    Do what: 取得 Redis client（必要時重建）
    How: 每次取用時讀 os.getenv("REDIS_URL")，若與快取不同就重建 client
    Why: .env / env 變動時，不要被 import 當下的值綁死，避免一直打到舊的 Upstash
    """
    global _REDIS_URL_CACHED, _RDS

    url = os.getenv("REDIS_URL", "").strip()
    if not url:
        # 沒設定就直接降級：不使用 redis
        return None

    if url != _REDIS_URL_CACHED or _RDS is None:
        _REDIS_URL_CACHED = url
        _RDS = redis.from_url(url, decode_responses=True)
        print("[landinfo] redis init url =", url)

    return _RDS


# 只在 import 時印一次目前 env（方便你確認「到底吃到哪條」）
print("[landinfo] effective REDIS_URL at import =", os.getenv("REDIS_URL"))


# =========
# Node enqueue
# =========
def enqueue_land_job(payload: dict):
    url = f"{NODE_LANDINFO_URL}/jobs"
    resp = requests.post(
        url,
        json=payload,
        headers={"x-job-token": NODE_JOB_TOKEN},
        timeout=15,
    )
    return resp


# =========
# Mode helpers
# =========
def _mode_key(user_id: str) -> str:
    return f"mode:landinfo:{user_id}"


def _parse_section_landno(text: str):
    """
    Do what: 解析「大利段 1306」或「大利段1306-0000」
    How: regex 分段名 + 地號主號 + optional 子號
    Why: 先做最穩定的純文字 MVP
    """
    msg = text.strip().replace("\u200b", "").replace("\n", "")

    # 注意：節點文字/輸入處理別塞奇怪符號，regex 已支援多種破折號
    m = re.match(r"^(.+?段)\s*([0-9]{1,4})(?:\s*[-－–—~～]\s*([0-9]{1,4}))?$", msg)
    if not m:
        return None

    section = m.group(1).strip()
    no1 = m.group(2)
    no2 = (m.group(3) or "").strip()
    land_no = f"{no1}-{no2}" if no2 else no1
    return section, land_no


async def _enter_mode(user_id: str):
    rds = get_redis()
    if not rds:
        return
    try:
        await rds.set(_mode_key(user_id), "1", ex=MODE_TTL)
        print("[redis] set", _mode_key(user_id), "ttl=", MODE_TTL)
    except Exception as e:
        # 不要讓 webhook 500：降級為「無狀態」
        print("[redis] set failed:", repr(e))


async def _exit_mode(user_id: str):
    rds = get_redis()
    if not rds:
        return
    try:
        await rds.delete(_mode_key(user_id))
        print("[redis] del", _mode_key(user_id))
    except Exception as e:
        print("[redis] delete failed:", repr(e))


async def _in_mode(user_id: str) -> bool:
    rds = get_redis()
    if not rds:
        return False
    try:
        v = await rds.get(_mode_key(user_id))
        print("[redis] get", _mode_key(user_id), "=>", v)
        return v == "1"
    except Exception as e:
        print("[redis] get failed:", repr(e))
        return False


# =========
# Handler
# =========
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

    # 2) 判斷是否為合法地號格式（大利段1306）
    parsed = _parse_section_landno(msg)

    # 不是合法格式：如果不在 mode 就放行；在 mode 則提示格式
    if not parsed:
        if not await _in_mode(user_id):
            return False

        # 在 mode 裡但格式不對
        await _enter_mode(user_id)  # 延長 TTL，避免使用者打錯就掉 mode
        reply_message(reply_token, [{
            "type": "text",
            "text": "格式不對喔，請輸入：大利段 1306（或 大利段 1306-0000）\n離開請輸入：取消"
        }])
        return True

    # 是合法地號：可選，順便進 mode（保留上下文）
    await _enter_mode(user_id)

    # 3) 成功解析：開始派工
    section, land_no = parsed

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

        resp = enqueue_land_job(payload)

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
