//用「最小測試」確認 Upstash 真的連得上

// helpers/ping-redis.js
const path = require("path");
require("dotenv").config({ path: path.resolve(__dirname, "../../.env") });

const IORedis = require("ioredis");

const url = process.env.REDIS_URL;
console.log("DEBUG REDIS_URL =", url); // 先印出來確認

if (!url) {
  console.error("❌ REDIS_URL is missing (dotenv did not load .env)");
  process.exit(1);
}

const isTLS = url.startsWith("rediss://");

const r = new IORedis(url, {
  maxRetriesPerRequest: 1,
  enableReadyCheck: false,
  ...(isTLS ? { tls: {} } : {}),
});

(async () => {
  try {
    const pong = await r.ping();
    console.log("✅ PING =>", pong);
  } catch (e) {
    console.error("❌ PING failed:", e);
  } finally {
    await r.quit();
  }
})();
