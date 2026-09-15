"""
Pharmacovigilance Module — National Pharmacovigilance Coordination Centre (NPvCC) Mandate.
Implements:
- AE/SAE capture with automatic regulatory deadline computation:
    * serious: report_date + 15 days
    * non_serious: report_date + 30 days
- Rolling 30-day safety signal detection algorithm (count >= 3 flags HIGH signal)
- Overdue regulatory deadline monitoring
- WHO-UMC causality assessment workflow
- DSMB aggregate safety feed
"""

import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import AdverseEvent, Patient, ResearchStudy, User
from app.routers.auth import get_current_user, require_role
from app.schemas import (
    AdverseEventCreate,
    AdverseEventOut,
    AdverseEventStatusUpdate,
    AESummaryOut,
    SafetySignalOut,
    WHOUMCCausalityUpdate,
)

router = APIRouter(prefix="/ae", tags=["pharmacovigilance"])

SYNTHETIC_MEDDRA_TERMS = {
    "elevated_alt",
    "hepatotoxicity",
    "nausea",
    "headache",
    "rash",
    "vomiting",
    "fatigue",
    "pruritus",
    "dizziness",
    "abdominal_pain",
    "diarrhea",
    "fever",
    "insomnia",
    "arthralgia",
    "myalgia",
    "anorexia",
    "dyspepsia",
    "tremor",
    "cough",
    "constipation",
    "urticaria",
    "palpitations",
    "hypotension",
}

WHO_UMC_CATEGORIES = {
    "certain",
    "probable",
    "possible",
    "unlikely",
    "unclassified",
    "unclassifiable",
}


def _to_ae_out(ae: AdverseEvent) -> AdverseEventOut:
    today = date.today()
    is_overdue = (ae.status not in ("resolved", "reported")) and (ae.regulatory_deadline < today)
    return AdverseEventOut(
        id=ae.id,
        study_id=ae.study_id,
        patient_id=ae.patient_id,
        description=ae.description,
        seriousness=ae.seriousness,
        outcome=ae.outcome,
        onset_date=ae.onset_date,
        report_date=ae.report_date,
        regulatory_deadline=ae.regulatory_deadline,
        reported_by=ae.reported_by,
        status=ae.status,
        ae_term=ae.ae_term,
        causality=ae.causality,
        action_taken=ae.action_taken,
        is_overdue=is_overdue,
    )


@router.get("/terms", response_model=List[str])
def list_synthetic_meddra_terms():
    """Returns the synthetic MedDRA stub term library for dropdown entry."""
    return sorted(list(SYNTHETIC_MEDDRA_TERMS))


@router.post("", response_model=AdverseEventOut, status_code=status.HTTP_201_CREATED)
def report_adverse_event(
    payload: AdverseEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "pharmacovigilance", "admin")),
):
    """
    Log an AE/SAE. Auto-calculates regulatory deadline before INSERT:
    - serious: report_date + 15 days
    - non_serious: report_date + 30 days
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == payload.study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if payload.seriousness not in ("serious", "non_serious"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seriousness must be 'serious' or 'non_serious'",
        )

    ae_term = payload.ae_term
    if ae_term:
        cleaned_term = ae_term.strip().lower().replace(" ", "_").replace("-", "_")
        ae_term = cleaned_term

    causality = payload.causality
    if causality and causality.lower() in WHO_UMC_CATEGORIES:
        causality = causality.lower()

    report_dt = payload.report_date or date.today()

    # --- AUTO-CALCULATE REGULATORY DEADLINE BEFORE INSERT ---
    if payload.seriousness == "serious":
        reg_deadline = report_dt + timedelta(days=15)
    else:
        reg_deadline = report_dt + timedelta(days=30)

    ae = AdverseEvent(
        study_id=payload.study_id,
        patient_id=payload.patient_id,
        description=payload.description,
        seriousness=payload.seriousness,
        outcome=payload.outcome or "recovering",
        onset_date=payload.onset_date or report_dt,
        report_date=report_dt,
        regulatory_deadline=reg_deadline,
        reported_by=current_user.id,
        status="open",
        ae_term=ae_term,
        causality=causality,
        action_taken=payload.action_taken,
        reporter_role=current_user.role,
    )
    db.add(ae)
    db.commit()
    db.refresh(ae)

    log_action(
        db,
        user_id=current_user.id,
        action="AE_REPORT",
        entity_type="adverse_event",
        entity_id=ae.id,
        new_value={
            "seriousness": ae.seriousness,
            "report_date": str(ae.report_date),
            "regulatory_deadline": str(ae.regulatory_deadline),
            "ae_term": ae.ae_term,
            "causality": ae.causality,
        },
    )

    return _to_ae_out(ae)


@router.get("/signals", response_model=List[SafetySignalOut])
def detect_safety_signals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    NPvCC STATUTORY SAFETY SIGNAL DETECTION ALGORITHM:
    Evaluates rolling 30-day window for recurring AE terms.
    If occurrences >= 3 within 30 days for a given study and AE term,
    surfaces an active Safety Signal Alert for DSMB and PV review.
    """
    today = date.today()
    window_start = today - timedelta(days=30)

    # Fetch all AEs in the rolling 30-day window
    recent_aes = (
        db.query(AdverseEvent)
        .filter(
            AdverseEvent.report_date >= window_start,
            AdverseEvent.ae_term.isnot(None),
        )
        .all()
    )

    # Group by (study_id, ae_term)
    grouped = {}
    for ae in recent_aes:
        key = (ae.study_id, ae.ae_term)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(ae)

    signals = []
    for (study_id, term), events in grouped.items():
        if len(events) >= 3:
            study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
            study_title = study.title if study else f"Study {str(study_id)[:8]}"
            intervention = (study.ayurvedic_intervention if study else None) or (study.title if study else "Herbal Formulation")

            earliest = min(e.report_date for e in events)
            latest = max(e.report_date for e in events)

            signals.append(
                SafetySignalOut(
                    study_id=study_id,
                    study_title=study_title,
                    ae_term=term.replace("_", " ").title(),
                    count_in_30_days=len(events),
                    earliest_date=earliest,
                    latest_date=latest,
                    signal_level="HIGH",
                    intervention=intervention,
                    recommendation=(
                        f"Immediate DSMB safety review and batch quality audit recommended per NPvCC guidelines. "
                        f"Detected {len(events)} cases of '{term.replace('_', ' ')}' within 30 days."
                    ),
                )
            )

    return signals


@router.get("/overdue", response_model=List[AdverseEventOut])
def list_overdue_aes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacovigilance", "admin", "ethics_committee", "pi")),
):
    """
    Returns all adverse events whose statutory regulatory deadline has passed
    without resolution or regulatory submission.
    """
    today = date.today()
    overdue_events = (
        db.query(AdverseEvent)
        .filter(
            AdverseEvent.regulatory_deadline < today,
            ~AdverseEvent.status.in_(["resolved", "reported"]),
        )
        .order_by(AdverseEvent.regulatory_deadline.asc())
        .all()
    )
    return [_to_ae_out(e) for e in overdue_events]


@router.patch("/{ae_id}/causality", response_model=AdverseEventOut)
def assess_who_umc_causality(
    ae_id: uuid.UUID,
    payload: WHOUMCCausalityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacovigilance", "admin", "pi")),
):
    """
    Updates the WHO-UMC causality classification for an Adverse Event.
    Categories: certain, probable, possible, unlikely, unclassified, unclassifiable.
    """
    ae = db.query(AdverseEvent).filter(AdverseEvent.id == ae_id).first()
    if not ae:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adverse event not found")

    causality_norm = payload.causality.strip().lower()
    if causality_norm not in WHO_UMC_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Causality must be one of {sorted(list(WHO_UMC_CATEGORIES))}",
        )

    old_causality = ae.causality
    ae.causality = causality_norm
    if payload.action_taken:
        ae.action_taken = payload.action_taken

    db.commit()
    db.refresh(ae)

    log_action(
        db,
        user_id=current_user.id,
        action="CAUSALITY_UPDATE",
        entity_type="adverse_event",
        entity_id=ae.id,
        old_value={"causality": old_causality},
        new_value={
            "causality": ae.causality,
            "action_taken": ae.action_taken,
            "comments": payload.comments,
        },
    )

    return _to_ae_out(ae)


@router.get("", response_model=List[AdverseEventOut])
def list_adverse_events(
    study_id: Optional[uuid.UUID] = Query(default=None),
    seriousness: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    PV & PI AE Inbox: Deadline-sorted (nearest deadline first).
    PIs only see events for their own studies.
    """
    query = db.query(AdverseEvent)

    if current_user.role == "pi":
        my_study_ids = [
            s.id
            for s in db.query(ResearchStudy.id)
            .filter(ResearchStudy.principal_investigator_id == current_user.id)
            .all()
        ]
        query = query.filter(AdverseEvent.study_id.in_(my_study_ids))

    if study_id:
        query = query.filter(AdverseEvent.study_id == study_id)
    if seriousness:
        query = query.filter(AdverseEvent.seriousness == seriousness)
    if status_filter:
        query = query.filter(AdverseEvent.status == status_filter)

    events = query.order_by(AdverseEvent.regulatory_deadline.asc()).all()
    return [_to_ae_out(e) for e in events]


@router.get("/dsmb/feed", response_model=List[AdverseEventOut])
def dsmb_safety_signal_feed(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacovigilance", "ethics_committee", "admin", "regulator", "pi")),
):
    """
    Data and Safety Monitoring Board (DSMB) aggregate safety feed across the entire portfolio.
    Surfaces all serious AEs and upcoming regulatory deadlines.
    """
    events = (
        db.query(AdverseEvent)
        .order_by(AdverseEvent.seriousness.desc(), AdverseEvent.regulatory_deadline.asc())
        .all()
    )
    return [_to_ae_out(e) for e in events]


@router.get("/summary/{study_id}", response_model=AESummaryOut)
def get_study_ae_summary(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = db.query(AdverseEvent).filter(AdverseEvent.study_id == study_id).all()
    today = date.today()

    total = len(events)
    serious = sum(1 for e in events if e.seriousness == "serious")
    non_serious = sum(1 for e in events if e.seriousness == "non_serious")
    overdue = sum(1 for e in events if (e.status not in ("resolved", "reported")) and (e.regulatory_deadline < today))
    open_count = sum(1 for e in events if e.status == "open")
    resolved = sum(1 for e in events if e.status in ("resolved", "reported"))

    return AESummaryOut(
        study_id=study_id,
        total_ae_count=total,
        serious_count=serious,
        non_serious_count=non_serious,
        overdue_count=overdue,
        open_count=open_count,
        resolved_count=resolved,
    )


@router.get("/{ae_id}", response_model=AdverseEventOut)
def get_adverse_event(
    ae_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ae = db.query(AdverseEvent).filter(AdverseEvent.id == ae_id).first()
    if not ae:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adverse event not found")
    return _to_ae_out(ae)


@router.put("/{ae_id}/status", response_model=AdverseEventOut)
def update_ae_status(
    ae_id: uuid.UUID,
    payload: AdverseEventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pharmacovigilance", "admin", "pi")),
):
    ae = db.query(AdverseEvent).filter(AdverseEvent.id == ae_id).first()
    if not ae:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Adverse event not found")

    if payload.status not in ("open", "under_review", "resolved", "reported"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be one of: open, under_review, resolved, reported",
        )

    old_status = ae.status
    ae.status = payload.status
    if payload.outcome:
        ae.outcome = payload.outcome

    db.commit()
    db.refresh(ae)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="adverse_event",
        entity_id=ae.id,
        old_value={"status": old_status},
        new_value={"status": ae.status, "outcome": ae.outcome},
    )

    return _to_ae_out(ae)
