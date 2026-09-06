"""
/studies routes — Chunk 1 (Study Tracker + KPIs), MVP build priority per
Section 3. Drop in as app/routers/studies.py.

Provides:
  GET  /studies       -> list studies, scoped by role (see RBAC note below)
  GET  /studies/{id}  -> single study with computed KPIs: enrollment
                         percent, full milestone list with overdue flags,
                         CTRI/IEC status
  POST /studies       -> create a study (pi or admin only)

RBAC scope note: the locked schema (Section 7) only has a single
principal_investigator_id FK on research_study — there's no
coordinator/monitor/EC/PV assignment table. So "Assigned study only"
(Section 4's Coordinator/Monitor row) can't be enforced at the query
level with the current schema; those roles currently see every study,
same as admin/regulator. Only the PI row is actually scoped (to their
own studies), because that's the one relationship the schema supports.
Flag this as a known scope gap if a judge asks, or add a study_team
join table later if there's time — not something to silently claim as
done.

Every CREATE writes to audit_trail via app.audit_log.log_action(), same
pattern as the LOGIN row in app/routers/auth.py.
"""

import uuid
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import Milestone, ResearchStudy, User
from app.routers.auth import get_current_user, require_role
from app.schemas import MilestoneOut, StudyCreate, StudyDetailOut, StudyOut

router = APIRouter(prefix="/studies", tags=["studies"])


def _enrollment_percent(study: ResearchStudy) -> float:
    if not study.enrollment_target:
        return 0.0
    return round(100 * study.enrolled_count / study.enrollment_target, 1)


def _to_study_out(study: ResearchStudy) -> StudyOut:
    return StudyOut(
        id=study.id,
        title=study.title,
        status=study.status,
        phase=study.phase,
        sponsor=study.sponsor,
        ctri_registration_number=study.ctri_registration_number,
        ctri_status=study.ctri_status,
        iec_approval_status=study.iec_approval_status,
        enrollment_target=study.enrollment_target,
        enrolled_count=study.enrolled_count,
        enrollment_percent=_enrollment_percent(study),
        site_id=study.site_id,
        principal_investigator_id=study.principal_investigator_id,
        start_date=study.start_date,
        end_date=study.end_date,
    )


@router.get("", response_model=List[StudyOut])
def list_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ResearchStudy)
    if current_user.role == "pi":
        query = query.filter(ResearchStudy.principal_investigator_id == current_user.id)
    studies = query.order_by(ResearchStudy.created_at.desc()).all()
    return [_to_study_out(s) for s in studies]


@router.get("/{study_id}", response_model=StudyDetailOut)
def get_study(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    if current_user.role == "pi" and study.principal_investigator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your study")

    milestones = (
        db.query(Milestone)
        .filter(Milestone.study_id == study.id)
        .order_by(Milestone.due_date.asc())
        .all()
    )
    today = date.today()
    milestone_outs = [
        MilestoneOut(
            id=m.id,
            milestone_type=m.milestone_type,
            due_date=m.due_date,
            completed_date=m.completed_date,
            status=m.status,
            is_overdue=(m.status != "completed" and m.due_date < today),
        )
        for m in milestones
    ]
    overdue_count = sum(1 for m in milestone_outs if m.is_overdue)

    return StudyDetailOut(
        **_to_study_out(study).model_dump(),
        milestones=milestone_outs,
        overdue_milestone_count=overdue_count,
    )


@router.post("", response_model=StudyOut, status_code=status.HTTP_201_CREATED)
def create_study(
    payload: StudyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "admin")),
):
    pi_id = payload.principal_investigator_id or (
        current_user.id if current_user.role == "pi" else None
    )
    if pi_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="principal_investigator_id is required when an admin creates a study",
        )

    study = ResearchStudy(
        title=payload.title,
        status="pending_iec",  # first of the 7 lifecycle stages, per Section 10
        phase=payload.phase,
        sponsor=payload.sponsor,
        ctri_registration_number=payload.ctri_registration_number,
        enrollment_target=payload.enrollment_target,
        enrolled_count=0,
        site_id=payload.site_id,
        principal_investigator_id=pi_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="research_study",
        entity_id=study.id,
        new_value={"title": study.title, "enrollment_target": study.enrollment_target},
    )

    return _to_study_out(study)
