from fastapi import APIRouter, HTTPException
from redis import Redis
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import logger
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = False
    redis_ok = False
    try:
        with engine.connect() as connection:
            connection.execute(select(1))
        db_ok = True
    except Exception as exc:
        logger.bind(exception=type(exc).__name__).warning(
            "Database health check failed"
        )
        db_ok = False
    try:
        redis_ok = bool(
            Redis.from_url(get_settings().redis_url, socket_connect_timeout=1).ping()
        )
    except Exception as exc:
        logger.bind(exception=type(exc).__name__).warning("Redis health check failed")
        redis_ok = False
    status = "ok" if db_ok and redis_ok else "degraded"
    if not db_ok:
        raise HTTPException(
            status_code=503,
            detail={"status": status, "database": db_ok, "redis": redis_ok},
        )
    return {"status": status, "db": db_ok, "redis": redis_ok}
