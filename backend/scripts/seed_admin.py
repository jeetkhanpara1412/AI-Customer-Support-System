import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.models import User
from app.db.session import SessionLocal, engine


def main() -> None:
    email = os.environ.get("FIRST_ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("FIRST_ADMIN_PASSWORD", "")
    if not email or len(password) < 10:
        raise SystemExit(
            "Set FIRST_ADMIN_EMAIL and a FIRST_ADMIN_PASSWORD of at least 10 characters."
        )
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            db.add(
                User(
                    email=email,
                    full_name="Support Administrator",
                    password_hash=hash_password(password),
                    role="admin",
                )
            )
            db.commit()
            print("Administrator account created.")
        elif user.role != "admin":
            user.role = "admin"
            db.commit()
            print("Existing account promoted to administrator.")
        else:
            print("Administrator account already exists.")


if __name__ == "__main__":
    main()
