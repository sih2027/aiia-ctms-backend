import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Project root = aiia-ctms-backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Load .env from project root
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


# Read database connection URL
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        f"DATABASE_URL is not configured.\n"
        f"Expected .env file at:\n{ENV_FILE}"
    )


# SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# Database session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for ORM models
Base = declarative_base()


# FastAPI database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()