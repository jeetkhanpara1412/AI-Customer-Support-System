from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

password_context = CryptContext(schemes=["argon2"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    return jwt.encode(
        {"sub": subject, "type": token_type, "iat": now, "exp": now + expires_delta},
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def create_access_token(subject: str) -> str:
    return create_token(
        subject, "access", timedelta(minutes=get_settings().access_token_minutes)
    )


def create_refresh_token(subject: str) -> str:
    return create_token(subject, "refresh", timedelta(days=get_settings().refresh_token_days))


def decode_token(token: str, expected_type: str = "access") -> str:
    payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
    if payload.get("type") != expected_type or not payload.get("sub"):
        raise jwt.InvalidTokenError("Invalid token type")
    return str(payload["sub"])
