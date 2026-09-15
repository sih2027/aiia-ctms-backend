import contextlib
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers import (
    abdm,
    ae,
    audit,
    auth,
    export,
    fhir,
    monitoring,
    notifications,
    patients,
    queries,
    studies,
)
from app.scheduler import shutdown_scheduler, start_scheduler


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: start background APScheduler for Merkle anchor commits and sweeps
    start_scheduler()
    yield
    # Shutdown: clean shutdown of scheduler
    shutdown_scheduler()


app = FastAPI(title="AIIA CTMS API (AAYUR SATHI)", lifespan=lifespan)

# Enable CORS for frontend web application
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all application routers
app.include_router(auth.router)
app.include_router(studies.router)
app.include_router(patients.router)
app.include_router(ae.router)
app.include_router(audit.router)
app.include_router(fhir.router)
app.include_router(export.router)
app.include_router(queries.router)
app.include_router(monitoring.router)
app.include_router(notifications.router)
app.include_router(abdm.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "AAYUR SATHI (AIIA CTMS)",
        "hindi_name": "आयुर साथी",
        "institution": "All India Institute of Ayurveda",
    }


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT COUNT(*) FROM users"))
    count = result.scalar()
    return {"connected": True, "users_table_row_count": count}