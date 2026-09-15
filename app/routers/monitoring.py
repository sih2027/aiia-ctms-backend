"""
Monitoring Visit Router — ALCOA+ Site Monitoring Reports for GCP Monitors / CRAs.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import MonitoringVisit, ResearchStudy, User
from app.routers.auth import get_current_user, require_role
from app.schemas import MonitoringVisitCreate, MonitoringVisitOut

router = APIRouter(prefix="/monitoring-visits", tags=["monitoring"])


def _to_monitoring_out(db: Session, mv: MonitoringVisit) -> MonitoringVisitOut:
    monitor = db.query(User).filter(User.id == mv.monitor_id).first()
    return MonitoringVisitOut(
        id=mv.id,
        study_id=mv.study_id,
        monitor_id=mv.monitor_id,
        monitor_name=monitor.name if monitor else None,
        visit_date=mv.visit_date,
        visit_type=mv.visit_type,
        findings=mv.findings,
        issues_identified=mv.issues_identified,
        follow_up_required=mv.follow_up_required,
        report_submitted_at=mv.report_submitted_at,
        created_at=mv.created_at,
    )


@router.post("", response_model=MonitoringVisitOut, status_code=status.HTTP_201_CREATED)
def record_monitoring_visit(
    payload: MonitoringVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("monitor", "admin")),
):
    """
    Submit an ALCOA+ site monitoring visit report (initiation, routine, for_cause, close_out).
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == payload.study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    mv = MonitoringVisit(
        study_id=payload.study_id,
        monitor_id=current_user.id,
        visit_date=payload.visit_date,
        visit_type=payload.visit_type,
        findings=payload.findings,
        issues_identified=payload.issues_identified,
        follow_up_required=payload.follow_up_required,
    )
    db.add(mv)
    db.commit()
    db.refresh(mv)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="monitoring_visit",
        entity_id=mv.id,
        new_value={
            "visit_type": mv.visit_type,
            "visit_date": str(mv.visit_date),
            "follow_up_required": mv.follow_up_required,
        },
    )

    return _to_monitoring_out(db, mv)


@router.get("", response_model=List[MonitoringVisitOut])
def list_monitoring_visits(
    study_id: Optional[uuid.UUID] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(MonitoringVisit)
    if study_id:
        query = query.filter(MonitoringVisit.study_id == study_id)

    visits = query.order_by(MonitoringVisit.visit_date.desc()).all()
    return [_to_monitoring_out(db, v) for v in visits]
