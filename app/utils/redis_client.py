import os
from redis.asyncio import Redis

_redis: Redis | None = None

def get_redis() -> Redis:
    global _redis
    if _redis is None:
        url = os.getenv("REDIS_URL")
        if not url:
            raise RuntimeError("REDIS_URL missing in .env")
        _redis = Redis.from_url(url, decode_responses=True)
    return _redis
