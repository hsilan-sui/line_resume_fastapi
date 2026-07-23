//用 Redis 做「30 分鐘窗口」+「每 userId 計數」
// do what：每個 userId 在 30 分鐘內最多 3 次，超過回 429
// how：Redis INCR + PEXPIRE（用 Lua 保證原子性）
// why：避免競態（同時多次請求）造成計數不準

// src/middlewares/rateLimitRedis.js
const Redis = require("ioredis");

let redis;

/** 建議：用 lazyConnect，避免 require 時就連線 */
function getRedis() {
  if (redis) return redis;

  const url = process.env.REDIS_URL;
  if (!url) throw new Error("REDIS_URL is not set");

  redis = new Redis(url, {
    maxRetriesPerRequest: 1,
    enableReadyCheck: true,
  });

  redis.on("error", (e) => {
    console.error("[redis] error:", e?.message || e);
  });

  return redis;
}

const LUA_INCR_EXPIRE = `
local current = redis.call('INCR', KEYS[1])
if tonumber(current) == 1 then
  redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
return current
`;

function rateLimitByUserId() {
  const MAX = Number(process.env.RATE_LIMIT_MAX || 3);
  const WINDOW_MS = Number(process.env.RATE_LIMIT_WINDOW_MS || 30 * 60 * 1000);

  return async (req, res, next) => {
    try {
      const userId = req.body?.userId;
      if (!userId) return res.status(400).json({ message: "userId is required" });

      // key 例：rl:landinfo:Uxxxxxxxx
      const key = `rl:landinfo:${userId}`;

      const r = getRedis();
      const count = await r.eval(LUA_INCR_EXPIRE, 1, key, String(WINDOW_MS));

      if (Number(count) > MAX) {
        const ttlMs = await r.pttl(key);
        const retryAfterSec = Math.max(1, Math.ceil(ttlMs / 1000));
        return res.status(429).json({
          message: `rate limited: ${MAX} per ${Math.round(WINDOW_MS / 60000)} minutes`,
          retryAfterSec,
        });
      }

      next();
    } catch (e) {
      console.error("[rateLimit] error:", e?.stack || e);
      // 你要更嚴格可改成 503；demo 我建議「限流壞了也先放行」避免 demo 掛掉
      next();
    }
  };
}

module.exports = { rateLimitByUserId };
