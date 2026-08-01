"""
One-time dev bootstrap: creates the initial admin account plus a couple of
reference rows (semester/scheme) so the UI isn't empty on first login.

Usage:
    python -m scripts.seed_admin
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.session import Base, engine, SessionLocal  # noqa: E402
import models  # noqa: E402,F401
from models.user import User  # noqa: E402
from models.academic import Semester, Scheme  # noqa: E402
from models.enums import UserRole  # noqa: E402
from auth.security import hash_password  # noqa: E402


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            admin = User(
                username="admin",
                email="admin@institute.edu",
                full_name="System Administrator",
                hashed_password=hash_password("ChangeMe@123"),
                role=UserRole.ADMIN,
                department="Administration",
            )
            db.add(admin)
            print("Created admin user -> username: admin | password: ChangeMe@123")
        else:
            print("Admin user already exists, skipping.")

        if not db.query(Semester).first():
            for i in range(1, 9):
                db.add(Semester(name=f"Semester {i}", number=i))
            print("Seeded semesters 1-8.")

        if not db.query(Scheme).first():
            db.add(Scheme(name="2022 Scheme", year=2022, is_active=True))
            print("Seeded default scheme.")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()
