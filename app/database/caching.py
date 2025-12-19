import redis.asyncio as redis
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
    except redis.ConnectionError as exc:
        raise ConnectionError("Could not connect to Redis server") from exc
    return client
