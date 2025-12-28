import os
import httpx

API_BASE = "https://api.line.me"

LINE_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
RICHMENU_HOME_ID = os.getenv("RICHMENU_HOME_ID", "").strip()

def _auth_headers():
    return {"Authorization": f"Bearer {LINE_TOKEN}"}

async def link_richmenu_to_user(user_id: str, richmenu_id: str):
    """
    Do what: 將指定 richmenu 綁到指定 user
    How: 先 unlink（避免舊的 user richmenu 蓋過 default），再 link
    Why: default richmenu 有時不會立刻刷新；而 user 已綁舊 richmenu 時會永遠看不到 default
    """
    if not LINE_TOKEN:
        raise RuntimeError("Missing LINE_CHANNEL_ACCESS_TOKEN")
    if not richmenu_id:
        raise RuntimeError("Missing RICHMENU_HOME_ID")

    async with httpx.AsyncClient(timeout=15) as client:
        # 1) 先解除（若本來沒綁，LINE 可能回 404，忽略即可）
        try:
            await client.delete(
                f"{API_BASE}/v2/bot/user/{user_id}/richmenu",
                headers=_auth_headers(),
            )
        except Exception:
            pass

        # 2) 再綁定
        r = await client.post(
            f"{API_BASE}/v2/bot/user/{user_id}/richmenu/{richmenu_id}",
            headers=_auth_headers(),
        )
        r.raise_for_status()

async def ensure_user_has_home_richmenu(user_id: str):
    # 你可以在 follow 時呼叫這個
    await link_richmenu_to_user(user_id, RICHMENU_HOME_ID)
