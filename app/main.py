from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import auth

app = FastAPI(title="AIIA CTMS API")
app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "AIIA CTMS"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    return {"connected": True, "users_table_row_count": count}