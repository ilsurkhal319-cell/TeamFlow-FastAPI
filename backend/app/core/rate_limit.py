from collections.abc import Callable

from fastapi import HTTPException, Request, status
from redis import Redis

from app.core.config import settings


def rate_limit(scope: str, limit: int, window_seconds: int = 60) -> Callable:
    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"teamflow:ratelimit:{scope}:{client_ip}"
        try:
            redis = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
            count = redis.incr(key)
            if count == 1:
                redis.expire(key, window_seconds)
            redis.close()
        except Exception:
            return
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Слишком много запросов. Попробуйте позже.",
                headers={"Retry-After": str(window_seconds)},
            )

    return dependency
