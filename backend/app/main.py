import csv
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from app.api.routes import admin, auth, chat, health, tickets, ws
from app.core.config import get_settings
from app.core.logging import configure_logging, logger
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.models import KnowledgeEntry, User
from app.db.session import SessionLocal, engine
from app.ml.train import DATA_PATH
from app.services.chat_service import initialize_ml


@asynccontextmanager
async def lifespan(_: FastAPI):
    if get_settings().env.lower() == "test":
        Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(KnowledgeEntry.id).limit(1)) is None and DATA_PATH.exists():
            with DATA_PATH.open(encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    db.add(
                        KnowledgeEntry(
                            message=row["Customer Message"],
                            category=row["Category"],
                            response=row["Company Response"],
                        )
                    )
            db.commit()
        settings = get_settings()
        if settings.first_admin_email and settings.first_admin_password:
            existing = db.scalar(select(User).where(User.email == settings.first_admin_email.lower()))
            if existing is None:
                from app.core.security import hash_password

                db.add(
                    User(
                        email=settings.first_admin_email.lower(),
                        full_name="Support Administrator",
                        password_hash=hash_password(settings.first_admin_password),
                        role="admin",
                    )
                )
                db.commit()
        initialize_ml(db)
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    application = FastAPI(title="AI Customer Support System", version="1.0.0", lifespan=lifespan)
    application.state.limiter = limiter

    @application.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        codes = {401: "unauthorized", 403: "forbidden", 404: "not_found", 409: "conflict", 429: "rate_limited"}
        message = exc.detail if isinstance(exc.detail, str) else "Request could not be completed"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": codes.get(exc.status_code, "request_error"), "message": message}},
            headers=exc.headers,
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_error", "message": "Invalid request data"}},
        )

    @application.exception_handler(RateLimitExceeded)
    async def rate_limit_error(_: Request, __: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"error": {"code": "rate_limited", "message": "Too many requests; please try again later"}},
        )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )

    @application.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
            "script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; connect-src 'self' ws: wss:"
        )
        if settings.env.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.bind(path=request.url.path, exception=type(exc).__name__).error("Unhandled request error")
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "An unexpected error occurred"}},
        )

    application.include_router(auth.router, prefix="/api")
    application.include_router(chat.router, prefix="/api")
    application.include_router(tickets.router, prefix="/api")
    application.include_router(admin.router, prefix="/api")
    application.include_router(health.router, prefix="/api")
    application.include_router(ws.router)
    return application


app = create_app()
