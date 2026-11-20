from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.models import User
from app.services.bootstrap import seed_users


def _session() -> tuple[Session, object]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    return Session(engine), engine


def test_development_seed_is_idempotent_and_creates_demo_user(capsys):
    settings = Settings(
        _env_file=None,
        env="development",
        admin_email="admin@example.com",
        admin_password="DevelopmentAdmin123!",
        admin_name="Configured Admin",
        demo_user_email="demo@example.com",
        demo_user_password="DemoUser123!",
        demo_user_name="Demo Customer",
    )
    db, engine = _session()
    try:
        seed_users(db, settings)
        seed_users(db, settings)
        users = db.scalars(select(User).order_by(User.email)).all()
        assert [(user.email, user.role) for user in users] == [
            ("admin@example.com", "admin"),
            ("demo@example.com", "user"),
        ]
        assert users[0].full_name == "Configured Admin"
        output = capsys.readouterr().out
        assert "admin@example.com" in output
        assert "DevelopmentAdmin123!" not in output
    finally:
        db.close()
        engine.dispose()


def test_non_development_seed_does_not_create_demo_user():
    settings = Settings(
        _env_file=None,
        env="production",
        jwt_secret="a-production-signing-secret-with-32-chars",
        admin_email="admin@example.com",
        admin_password="DevelopmentAdmin123!",
        demo_user_email="demo@example.com",
        demo_user_password="DemoUser123!",
    )
    db, engine = _session()
    try:
        seed_users(db, settings)
        users = db.scalars(select(User)).all()
        assert [(user.email, user.role) for user in users] == [
            ("admin@example.com", "admin")
        ]
    finally:
        db.close()
        engine.dispose()
