import hashlib
import threading

import jwt
from fastapi import HTTPException, Request
from redis import Redis
from slowapi import Limiter

from app.core.config import get_settings
from app.core.logging import logger
from app.core.security import decode_token

_local_email_attempts: dict[str, int] = {}
_local_email_lock = threading.Lock()


def rate_limit_key(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        try:
            return f"user:{decode_token(authorization[7:].strip())}"
        except jwt.PyJWTError:
            pass
    return request.client.host if request.client else "unknown"


_settings = get_settings()
limiter = Limiter(
    key_func=rate_limit_key,
    default_limits=["120/minute"],
    storage_uri="memory://" if _settings.env.lower() == "test" else _settings.redis_url,
)


def enforce_email_limit(email: str, action: str) -> None:
    settings = get_settings()
    hashed_email = hashlib.sha256(email.lower().encode()).hexdigest()
    key = f"auth:{action}:{hashed_email}"
    if settings.env.lower() == "test":
        with _local_email_lock:
            _local_email_attempts[key] = _local_email_attempts.get(key, 0) + 1
            attempts = _local_email_attempts[key]
    else:
        try:
            store = Redis.from_url(settings.redis_url, socket_connect_timeout=1)
            attempts = store.incr(key)
            if attempts == 1:
                store.expire(key, 60)
        except Exception as exc:
            logger.bind(exception=type(exc).__name__, action=action).error("Authentication rate-limit storage unavailable")
            raise HTTPException(status_code=503, detail="Authentication temporarily unavailable") from exc
    if attempts > 5:
        raise HTTPException(status_code=429, detail="Too many requests; please try again later")
