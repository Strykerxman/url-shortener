import redis.asyncio as redis
import asyncio
from app.core import logging
from app.core.config import get_settings

settings = get_settings()

pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)

async def get_redis() -> redis.Redis:
    client: redis.Redis = redis.Redis(connection_pool=pool)
    try:
        await client.ping()
    except Exception as e:
        logging.logger.warning("Redis ping failed during connection; continuing without cache. Error: %s", e, exc_info=True)
    return client

async def safe_redis_set(client: redis.Redis, key: str, value: str, ex: int):
    try:
        await asyncio.wait_for(client.set(key, value, ex=ex), timeout=0.75)
    except asyncio.TimeoutError as e:
        logging.logger.warning("Timed out setting Redis key=%s", key)
    except Exception:
        logging.logger.exception("Error setting Redis key=%s", key)    