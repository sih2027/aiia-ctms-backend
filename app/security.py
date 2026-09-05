"""
Password hashing and JWT helpers for the AIIA CTMS backend.

Drop in as app/security.py. Reads JWT_SECRET_KEY from .env (add it —
it is NOT in your existing .env yet, only DATABASE_URL is). Generate
one with: python -c "import secrets; print(secrets.token_hex(32))"
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import jwt, JWTError
from passlib.context import CryptContext

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Add it to your .env file "
        '(e.g. JWT_SECRET_KEY=<output of `python -c "import secrets; print(secrets.token_hex(32))"`).'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours — long enough for a demo day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(user_id: str, role: str) -> str:
    """
    Encodes user_id (sub) and role into the JWT payload, per Section 2's
    auth requirement: "Role embedded in token payload; server-side
    validation on every route."
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Raises jose.JWTError if the token is invalid or expired."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])