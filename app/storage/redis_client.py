import redis
from app.core.config import REDIS_URL

# Single shared Redis connection (IMPORTANT)
r = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)