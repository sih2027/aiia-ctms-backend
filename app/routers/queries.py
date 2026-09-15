"""
Clinical Data Query Engine — GCP Monitor Query Raise / Answer / Close Lifecycle.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import DataQuery, Patient, ResearchStudy, User, VisitLog
from app.routers.auth import get_current_user, require_role
from app.schemas import DataQueryAnswer, DataQueryClose, DataQueryCreate, DataQueryOut

router = APIRouter(prefix="/queries", tags=["queries"])


def _to_query_out(db: Session, q: DataQuery) -> DataQueryOut:
    raiser = db.query(User).filter(User.id == q.raised_by).first()
    resolver = db.query(User).filter(User.id == q.resolved_by).first() if q.resolved_by else None
    return DataQueryOut(
        id=q.id,
        study_id=q.study_id,
        patient_id=q.patient_id,
        visit_log_id=q.visit_log_id,
        raised_by=q.raised_by,
        raiser_name=raiser.name if raiser else None,
        resolved_by=q.resolved_by,
        resolver_name=resolver.name if resolver else None,
        field_name=q.field_name,
        query_text=q.query_text,
        resolution_text=q.resolution_text,
        status=q.status,
        created_at=q.created_at,
        resolved_at=q.resolved_at,
    )


@router.post("", response_model=DataQueryOut, status_code=status.HTTP_201_CREATED)
def raise_data_query(
    payload: DataQueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("monitor", "pi", "admin")),
):
    """
    GCP Monitor or CRA raises an electronic data query against a CRF field or visit log.
    Initial status: 'open'.
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == payload.study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    q = DataQuery(
        study_id=payload.study_id,
        patient_id=payload.patient_id,
        visit_log_id=payload.visit_log_id,
        raised_by=current_user.id,
        field_name=payload.field_name,
        query_text=payload.query_text,
        status="open",
    )
    db.add(q)
    db.commit()
    db.refresh(q)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="data_query",
        entity_id=q.id,
        new_value={"field_name": q.field_name, "query_text": q.query_text, "status": "open"},
    )

    return _to_query_out(db, q)


@router.get("", response_model=List[DataQueryOut])
def list_data_queries(
    study_id: Optional[uuid.UUID] = Query(default=None),
    patient_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(DataQuery)
    if study_id:
        query = query.filter(DataQuery.study_id == study_id)
    if patient_id:
        query = query.filter(DataQuery.patient_id == patient_id)
    if status_filter:
        query = query.filter(DataQuery.status == status_filter)

    queries = query.order_by(DataQuery.created_at.desc()).all()
    return [_to_query_out(db, q) for q in queries]


@router.patch("/{query_id}/answer", response_model=DataQueryOut)
def answer_data_query(
    query_id: uuid.UUID,
    payload: DataQueryAnswer,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    """
    Clinical Trial Coordinator responds to a monitor query with resolution text.
    Changes status to 'answered'.
    """
    q = db.query(DataQuery).filter(DataQuery.id == query_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")

    old_status = q.status
    q.status = "answered"
    q.resolution_text = payload.resolution_text
    q.resolved_by = current_user.id

    db.commit()
    db.refresh(q)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="data_query",
        entity_id=q.id,
        old_value={"status": old_status},
        new_value={"status": q.status, "resolution_text": q.resolution_text},
    )

    return _to_query_out(db, q)


@router.patch("/{query_id}/close", response_model=DataQueryOut)
def close_data_query(
    query_id: uuid.UUID,
    payload: DataQueryClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("monitor", "admin")),
):
    """
    GCP Monitor verifies the resolution and closes the query.
    Changes status to 'closed'.
    """
    q = db.query(DataQuery).filter(DataQuery.id == query_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Query not found")

    old_status = q.status
    q.status = "closed"
    q.resolved_at = datetime.utcnow()

    db.commit()
    db.refresh(q)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="data_query",
        entity_id=q.id,
        old_value={"status": old_status},
        new_value={"status": q.status, "resolved_at": str(q.resolved_at)},
    )

    return _to_query_out(db, q)
