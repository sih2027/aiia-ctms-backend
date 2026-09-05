"""
One-off script to seed the 7 test users (one per role) needed for the
Day-1 "done" condition in Section 13 of the master context doc:

    "Login returns correct JWT for all 7 test users."

Drop this in as app/seed_test_users.py (it needs to import app.database,
app.models, app.security, so it must live inside the app/ package).

Run from the repo root with your venv activated and .env already
containing DATABASE_URL + JWT_SECRET_KEY:

    python -m app.seed_test_users

Safe to re-run — any email that already exists is skipped, not
duplicated or overwritten.
"""

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

# Same password for every test user — this is throwaway seed data for a
# hackathon demo, not a real credential, so a shared password is fine.
TEST_PASSWORD = "Test@1234"

TEST_USERS = [
    {"name": "Dr. Asha Rao",      "email": "pi@aiia-ctms.com",          "role": "pi"},
    {"name": "Priya Nair",        "email": "coordinator@aiia-ctms.com", "role": "coordinator"},
    {"name": "Karan Mehta",       "email": "monitor@aiia-ctms.com",     "role": "monitor"},
    {"name": "Dr. Sunita Iyer",   "email": "ethics@aiia-ctms.com",      "role": "ethics_committee"},
    {"name": "Dr. Ramesh Pillai", "email": "pv@aiia-ctms.com",          "role": "pharmacovigilance"},
    {"name": "Anita Desai",       "email": "admin@aiia-ctms.com",       "role": "admin"},
    {"name": "Vikram Singh",      "email": "regulator@aiia-ctms.com",   "role": "regulator"},
]


def seed() -> None:
    db = SessionLocal()
    try:
        created, skipped = [], []
        for u in TEST_USERS:
            if db.query(User).filter(User.email == u["email"]).first():
                skipped.append(u["email"])
                continue
            db.add(
                User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=hash_password(TEST_PASSWORD),
                    role=u["role"],
                )
            )
            created.append(u["email"])
        db.commit()

        print(f"Created {len(created)} user(s):")
        for email in created:
            print(f"  + {email}")
        if skipped:
            print(f"\nSkipped {len(skipped)} already-existing user(s):")
            for email in skipped:
                print(f"  - {email}")
        print(f"\nAll test users share the password: {TEST_PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
