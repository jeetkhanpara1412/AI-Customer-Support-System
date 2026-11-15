import hmac
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.rate_limit import enforce_email_limit, limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.api import LoginRequest, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import normalize_email, refresh_token_digest

router = APIRouter(prefix="/auth", tags=["auth"])
_dummy_password_hash = hash_password("not-a-real-user-password")


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "refresh_token",
        token,
        httponly=True,
        secure=settings.env.lower() == "production",
        samesite="strict",
        max_age=settings.refresh_token_days * 86400,
        path="/api/auth",
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    email = normalize_email(str(payload.email))
    enforce_email_limit(email, "register")
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=409, detail="Unable to create account with those details"
        )
    user = User(
        email=email,
        full_name=payload.name,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    email = normalize_email(str(payload.email))
    enforce_email_limit(email, "login")
    user = db.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user else _dummy_password_hash
    valid_password = verify_password(payload.password, password_hash)
    now = datetime.now(UTC)
    locked_until = user.locked_until if user else None
    if locked_until and locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=UTC)
    locked = bool(locked_until and locked_until > now)
    if user is None or not valid_password or locked:
        if user and not locked:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.locked_until = now + timedelta(minutes=15)
            db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user.failed_login_attempts = 0
    user.locked_until = None
    refresh = create_refresh_token(str(user.id))
    user.refresh_token_hash = refresh_token_digest(refresh)
    db.commit()
    _set_refresh_cookie(response, refresh)
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    if request.headers.get("x-requested-with") != "fetch":
        raise HTTPException(status_code=403, detail="Refresh request rejected")
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh credentials required")
    try:
        user_id = int(decode_token(token, "refresh"))
    except (jwt.PyJWTError, ValueError):
        raise HTTPException(
            status_code=401, detail="Invalid refresh credentials"
        ) from None
    user = db.get(User, user_id)
    if (
        user is None
        or not user.refresh_token_hash
        or not hmac.compare_digest(user.refresh_token_hash, refresh_token_digest(token))
    ):
        raise HTTPException(status_code=401, detail="Invalid refresh credentials")
    refreshed_token = create_refresh_token(str(user.id))
    user.refresh_token_hash = refresh_token_digest(refreshed_token)
    db.commit()
    _set_refresh_cookie(response, refreshed_token)
    return {"access_token": create_access_token(str(user.id))}


@router.post("/logout", status_code=204)
def logout(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user.refresh_token_hash = None
    db.commit()
    response.delete_cookie(
        "refresh_token",
        path="/api/auth",
        httponly=True,
        secure=get_settings().env.lower() == "production",
        samesite="strict",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)):
    return user
