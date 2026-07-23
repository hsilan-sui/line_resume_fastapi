# Raspberry Pi Docker Compose Deployment

This stack runs:

- FastAPI LINE Bot on `fastapi:3000`
- Node landinfo server on `landinfo-server:3001`
- Node landinfo worker
- Redis
- optional Cloudflare Tunnel or ngrok

## Directory Layout

This repo is a monorepo:

```text
line_resume_fastapi/
  app/
  services/
    landinfo_api/
  deploy/
    raspi/
```

The compose file lives in:

```bash
~/line_resume_fastapi/deploy/raspi
```

## Raspberry Pi Setup

Install Docker:

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

Log out and back in, then enable Docker:

```bash
sudo systemctl enable docker
sudo systemctl start docker
```

## Configure

```bash
cd ~/line_resume_fastapi/deploy/raspi
cp .env.example .env
nano .env
```

Required values:

```text
LINE_CHANNEL_ACCESS_TOKEN
LINE_CHANNEL_SECRET
NODE_JOB_TOKEN
CF_WORKER_URL
WORKER_TOKEN
```

Use the same `NODE_JOB_TOKEN` for FastAPI and Node.

## Start

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
docker compose logs -f fastapi
docker compose logs -f landinfo-server
docker compose logs -f landinfo-worker
```

Health checks:

```bash
curl http://127.0.0.1:3000/
docker compose exec landinfo-server node -e "fetch('http://127.0.0.1:3001/health').then(async r => console.log(r.status, await r.text()))"
```

## Public HTTPS

LINE requires a public HTTPS webhook URL. Prefer Cloudflare Tunnel on Raspberry Pi:

```bash
docker compose --profile tunnel up -d cloudflared
```

Set the Cloudflare Tunnel public hostname to route to:

```text
http://fastapi:3000
```

Then set LINE Developers Webhook URL:

```text
https://your-domain.example.com/webhook
```

For temporary testing with ngrok:

```bash
docker compose --profile ngrok up -d ngrok
docker compose logs -f ngrok
```

ngrok free URLs change; Cloudflare Tunnel is better for always-on service.

### ngrok Discord Notifier

If you use a random ngrok URL, enable the notifier so you can receive the new URL while away from the Pi.

Set these values in `.env`:

```text
NGROK_AUTHTOKEN=...
DISCORD_WEBHOOK_URL=...
NGROK_NOTIFY_WEBHOOK_PATH=/webhook
```

Start ngrok and the notifier:

```bash
docker compose --profile ngrok up -d --build
docker compose logs -f ngrok-notifier
```

Discord will receive:

```text
Public URL: https://xxxx.ngrok-free.app
LINE Webhook URL: https://xxxx.ngrok-free.app/webhook
```

Then update LINE Developers > Messaging API > Webhook URL.

## Restart Policy

All long-running services use:

```yaml
restart: unless-stopped
```

After Raspberry Pi reboots, Docker starts the stack again as long as Docker itself is enabled.

## Update

```bash
cd ~/line_resume_fastapi
git pull
cd deploy/raspi
docker compose up -d --build
```
