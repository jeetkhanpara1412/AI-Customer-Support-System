from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

database_url = get_settings().database_url
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
pool_args = (
    {"poolclass": StaticPool}
    if database_url in {"sqlite://", "sqlite:///:memory:"}
    else {}
)
engine = create_engine(
    database_url, pool_pre_ping=True, connect_args=connect_args, **pool_args
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
