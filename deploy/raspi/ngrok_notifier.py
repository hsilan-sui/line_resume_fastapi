import json
import os
import time
import urllib.error
import urllib.request


NGROK_API_URL = os.getenv("NGROK_API_URL", "http://ngrok:4040/api/tunnels")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
WEBHOOK_PATH = os.getenv("NGROK_NOTIFY_WEBHOOK_PATH", "/webhook")
POLL_SECONDS = int(os.getenv("NGROK_NOTIFY_POLL_SECONDS", "30"))
STATE_FILE = os.getenv("NGROK_NOTIFY_STATE_FILE", "/state/last_url")


def request_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def post_discord(content):
    if not DISCORD_WEBHOOK_URL:
        print("[ngrok-notifier] DISCORD_WEBHOOK_URL is not set")
        return False

    body = json.dumps({"content": content}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "User-Agent": "Mozilla/5.0 ngrok-notifier/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        response.read()
        return 200 <= response.status < 300


def read_last_url():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            value = f.read().strip()
            if value:
                print("[ngrok-notifier] loaded state:", value)
            return value
    except FileNotFoundError:
        print("[ngrok-notifier] no previous state")
        return ""
    except OSError as e:
        print("[ngrok-notifier] cannot read state:", repr(e))
        return ""


def write_last_url(url):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(url)
        print("[ngrok-notifier] wrote state:", url)
    except OSError as e:
        print("[ngrok-notifier] cannot write state:", repr(e))


def first_https_tunnel(data):
    for tunnel in data.get("tunnels", []):
        public_url = str(tunnel.get("public_url", "")).strip()
        if public_url.startswith("https://"):
            return public_url.rstrip("/")
    return ""


def main():
    print("[ngrok-notifier] waiting for ngrok tunnel:", NGROK_API_URL)
    last_url = read_last_url()

    while True:
        try:
            data = request_json(NGROK_API_URL)
            public_url = first_https_tunnel(data)
            if not public_url:
                print("[ngrok-notifier] no https tunnel yet")
            elif public_url != last_url:
                webhook_url = f"{public_url}{WEBHOOK_PATH}"
                message = (
                    "ngrok URL changed for LINE Bot\n"
                    f"Public URL: {public_url}\n"
                    f"LINE Webhook URL: {webhook_url}\n"
                    "Update this in LINE Developers > Messaging API > Webhook URL."
                )
                if post_discord(message):
                    print("[ngrok-notifier] sent Discord notification:", webhook_url)
                    last_url = public_url
                    write_last_url(public_url)
                else:
                    last_url = public_url
                    print("[ngrok-notifier] skipped Discord send; suppressing duplicate for current process")
            else:
                print("[ngrok-notifier] tunnel unchanged:", public_url)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            print("[ngrok-notifier] waiting:", repr(e))
        except Exception as e:
            print("[ngrok-notifier] error:", repr(e))

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
