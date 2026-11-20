from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.db.models import User


def seed_users(db: Session, settings: Settings) -> None:
    if not settings.admin_email or not settings.admin_password:
        raise ValueError("Set ADMIN_EMAIL and ADMIN_PASSWORD before seeding.")
    if len(settings.admin_password) < 10:
        raise ValueError("ADMIN_PASSWORD must contain at least 10 characters.")

    admin_email = settings.admin_email.strip().lower()
    admin = db.scalar(select(User).where(User.email == admin_email))
    if admin is None:
        admin = User(
            email=admin_email,
            full_name=settings.admin_name.strip() or "Support Administrator",
            password_hash=hash_password(settings.admin_password),
            role="admin",
        )
        db.add(admin)
        db.commit()
    else:
        admin.full_name = settings.admin_name.strip() or "Support Administrator"
        admin.role = "admin"
        if not verify_password(settings.admin_password, admin.password_hash):
            admin.password_hash = hash_password(settings.admin_password)
        db.commit()
    print(f"Admin account ready: {admin_email}")

    if settings.env.lower() != "development":
        return
    if not settings.demo_user_email or not settings.demo_user_password:
        raise ValueError(
            "Set DEMO_USER_EMAIL and DEMO_USER_PASSWORD in development."
        )
    demo_email = settings.demo_user_email.strip().lower()
    if demo_email == admin_email:
        raise ValueError("DEMO_USER_EMAIL must differ from ADMIN_EMAIL.")
    if len(settings.demo_user_password) < 10:
        raise ValueError("DEMO_USER_PASSWORD must contain at least 10 characters.")

    demo_user = db.scalar(select(User).where(User.email == demo_email))
    if demo_user is None:
        db.add(
            User(
                email=demo_email,
                full_name=settings.demo_user_name.strip() or "Demo Customer",
                password_hash=hash_password(settings.demo_user_password),
                role="user",
            )
        )
        db.commit()
        return
    if demo_user.role == "admin":
        raise ValueError("DEMO_USER_EMAIL already belongs to an administrator.")
    demo_user.full_name = settings.demo_user_name.strip() or "Demo Customer"
    demo_user.role = "user"
    if not verify_password(settings.demo_user_password, demo_user.password_hash):
        demo_user.password_hash = hash_password(settings.demo_user_password)
    db.commit()
