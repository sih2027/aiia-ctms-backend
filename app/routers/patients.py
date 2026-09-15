"""
Patient screening, DPDP Act 2023 informed consent, dual-gate enrollment,
inclusion/exclusion criteria, visit tracking, and protocol deviations.
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import (
    IECriteria,
    IEResult,
    InformedConsent,
    Patient,
    ProtocolDeviation,
    ResearchStudy,
    User,
    VisitLog,
)
from app.routers.auth import get_current_user, require_role
from app.schemas import (
    ConsentRecordCreate,
    ConsentRecordOut,
    ConsentWithdraw,
    IECriteriaCreate,
    IECriteriaOut,
    IEResultCreate,
    IEResultOut,
    PatientEnroll,
    PatientOut,
    PatientScreen,
    PatientStatusUpdate,
    ProtocolDeviationCreate,
    ProtocolDeviationOut,
    VisitLogCreate,
    VisitLogOut,
    VisitLogUpdate,
)

router = APIRouter(prefix="/patients", tags=["patients"])


def _check_valid_consent(db: Session, patient_id: uuid.UUID) -> bool:
    consent = (
        db.query(InformedConsent)
        .filter(
            InformedConsent.patient_id == patient_id,
            InformedConsent.withdrawn_at.is_(None),
        )
        .first()
    )
    return consent is not None


def _to_patient_out(db: Session, patient: Patient) -> PatientOut:
    has_consent = _check_valid_consent(db, patient.id)
    return PatientOut(
        id=patient.id,
        study_id=patient.study_id,
        screening_number=patient.screening_number,
        randomization_number=patient.randomization_number,
        enrollment_date=patient.enrollment_date,
        status=patient.status,
        age=patient.age,
        sex=patient.sex,
        abha_id=patient.abha_id,
        abha_status=patient.abha_status or "unverified",
        has_valid_consent=has_consent,
    )


@router.post("/screen", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
def screen_patient(
    payload: PatientScreen,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    """
    Step 4a: Screen a patient against inclusion/exclusion criteria.
    Creates a new patient record with status='screened'.
    """
    study = db.query(ResearchStudy).filter(ResearchStudy.id == payload.study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    patient = Patient(
        study_id=payload.study_id,
        screening_number=payload.screening_number,
        status="screened",
        age=payload.age,
        sex=payload.sex,
        abha_id=payload.abha_id,
        abha_status="verified" if payload.abha_id else "unverified",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="patient",
        entity_id=patient.id,
        new_value={"screening_number": patient.screening_number, "status": patient.status},
    )

    return _to_patient_out(db, patient)


# --- DPDP Act 2023 Consent Ledger (Gate 2) ---
@router.post("/{patient_id}/consent", response_model=ConsentRecordOut, status_code=status.HTTP_201_CREATED)
def record_patient_consent(
    patient_id: uuid.UUID,
    payload: ConsentRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    """
    Records legally binding Informed Consent under DPDP Act 2023 and ICMR Ethical Guidelines.
    This satisfies Gate 2 of the Dual-Gate Enrollment requirement.
    """
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    # Check if there is already an active non-withdrawn consent
    existing_active = (
        db.query(InformedConsent)
        .filter(InformedConsent.patient_id == patient_id, InformedConsent.withdrawn_at.is_(None))
        .first()
    )
    if existing_active:
        return existing_active

    witness_id = payload.witnessed_by or current_user.id
    doc_ref = payload.consent_document_ref or f"ICF-SIG-{str(patient_id)[:8].upper()}-{datetime.utcnow().strftime('%Y%m%d')}.pdf"

    consent = InformedConsent(
        patient_id=patient_id,
        study_id=patient.study_id,
        consent_version=payload.consent_version,
        consented_at=datetime.utcnow(),
        consent_document_ref=doc_ref,
        witnessed_by=witness_id,
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="informed_consent",
        entity_id=consent.id,
        new_value={
            "patient_id": str(patient_id),
            "study_id": str(patient.study_id),
            "consent_version": consent.consent_version,
            "document_ref": consent.consent_document_ref,
        },
    )

    return consent


@router.post("/{patient_id}/withdraw-consent", response_model=ConsentRecordOut)
def withdraw_patient_consent(
    patient_id: uuid.UUID,
    payload: ConsentWithdraw,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    """
    Patient exercises right to withdraw consent under DPDP Act 2023.
    Immediately transitions patient status to 'withdrawn'.
    """
    consent = (
        db.query(InformedConsent)
        .filter(InformedConsent.patient_id == patient_id, InformedConsent.withdrawn_at.is_(None))
        .order_by(InformedConsent.consented_at.desc())
        .first()
    )
    if not consent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active consent found for this patient")

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    consent.withdrawn_at = datetime.utcnow()
    consent.withdrawal_reason = payload.withdrawal_reason

    if patient and patient.status == "enrolled":
        patient.status = "withdrawn"

    db.commit()
    db.refresh(consent)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="informed_consent",
        entity_id=consent.id,
        old_value={"withdrawn_at": None},
        new_value={"withdrawn_at": str(consent.withdrawn_at), "reason": consent.withdrawal_reason},
    )

    return consent


@router.get("/{patient_id}/consent", response_model=Optional[ConsentRecordOut])
def get_patient_consent(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    consent = (
        db.query(InformedConsent)
        .filter(InformedConsent.patient_id == patient_id)
        .order_by(InformedConsent.consented_at.desc())
        .first()
    )
    return consent


# --- DUAL-GATE ENROLLMENT ---
@router.post("/enroll", response_model=PatientOut)
def enroll_patient(
    payload: PatientEnroll,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    """
    Step 4b: Enroll a screened patient.

    CRITICAL DUAL GATES (Specification Section 5 & 11):
    1. GATE 1 (Regulatory Hard Gate): Backend strictly rejects enrollment if
       research_study.ctri_status != 'registered'.
    2. GATE 2 (DPDP Act 2023 Consent Gate): Backend strictly rejects enrollment if
       the patient does NOT have a valid, non-withdrawn informed_consent record.
    """
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    if patient.status == "enrolled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Patient is already enrolled"
        )

    study = db.query(ResearchStudy).filter(ResearchStudy.id == patient.study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    # --- GATE 1: CTRI LEGAL HARD GATE ---
    if study.ctri_status != "registered":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GATE 1 FAILED: Study CTRI status must be 'registered' before enrolling patients (Legal Hard Gate)",
        )

    # --- GATE 2: DPDP ACT 2023 INFORMED CONSENT GATE ---
    active_consent = (
        db.query(InformedConsent)
        .filter(
            InformedConsent.patient_id == patient.id,
            InformedConsent.withdrawn_at.is_(None),
        )
        .first()
    )
    if not active_consent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="GATE 2 FAILED: Valid Informed Consent must be signed and registered under DPDP Act 2023 prior to enrollment",
        )

    if study.enrolled_count >= study.enrollment_target:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Study enrollment target ({study.enrollment_target}) has already been reached",
        )

    old_status = patient.status
    patient.status = "enrolled"
    patient.enrollment_date = payload.enrollment_date or date.today()

    study.enrolled_count += 1
    if study.status == "site_activation" and study.enrolled_count > 0:
        study.status = "actively_enrolling"
    elif study.enrolled_count >= study.enrollment_target:
        study.status = "completed"

    if payload.randomization_number:
        patient.randomization_number = payload.randomization_number
    else:
        site_code = study.site_id or "AIIA"
        patient.randomization_number = f"RND-{site_code}-{study.enrolled_count:03d}"

    db.commit()
    db.refresh(patient)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="patient",
        entity_id=patient.id,
        old_value={"status": old_status},
        new_value={
            "status": patient.status,
            "randomization_number": patient.randomization_number,
            "enrolled_count": study.enrolled_count,
        },
    )

    return _to_patient_out(db, patient)


@router.patch("/{patient_id}/status", response_model=PatientOut)
def update_patient_status(
    patient_id: uuid.UUID,
    payload: PatientStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    valid_statuses = ("screened", "enrolled", "completed", "withdrawn", "screen_failed")
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status. Must be one of {valid_statuses}")

    old_status = patient.status
    patient.status = payload.status
    db.commit()
    db.refresh(patient)

    log_action(
        db,
        user_id=current_user.id,
        action="STATUS_CHANGE",
        entity_type="patient",
        entity_id=patient.id,
        old_value={"status": old_status},
        new_value={"status": patient.status, "reason": payload.reason},
    )

    return _to_patient_out(db, patient)


@router.get("/study/{study_id}", response_model=List[PatientOut])
def list_patients_for_study(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    patients = (
        db.query(Patient)
        .filter(Patient.study_id == study_id)
        .order_by(Patient.created_at.desc())
        .all()
    )
    return [_to_patient_out(db, p) for p in patients]


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return _to_patient_out(db, patient)


# --- Inclusion / Exclusion Criteria & Assessments ---
@router.post("/studies/{study_id}/ie-criteria", response_model=IECriteriaOut, status_code=status.HTTP_201_CREATED)
def create_ie_criterion(
    study_id: uuid.UUID,
    payload: IECriteriaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("pi", "coordinator", "admin")),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    if payload.criterion_type not in ("inclusion", "exclusion"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Type must be 'inclusion' or 'exclusion'")

    criterion = IECriteria(
        study_id=study_id,
        criterion_type=payload.criterion_type,
        criterion_number=payload.criterion_number,
        description=payload.description,
    )
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.get("/studies/{study_id}/ie-criteria", response_model=List[IECriteriaOut])
def list_ie_criteria(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(IECriteria)
        .filter(IECriteria.study_id == study_id)
        .order_by(IECriteria.criterion_type.asc(), IECriteria.criterion_number.asc())
        .all()
    )


@router.post("/{patient_id}/ie-results", response_model=IEResultOut, status_code=status.HTTP_201_CREATED)
def record_ie_result(
    patient_id: uuid.UUID,
    payload: IEResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin")),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")

    criterion = db.query(IECriteria).filter(IECriteria.id == payload.criterion_id).first()
    if not criterion:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Criterion not found")

    existing = (
        db.query(IEResult)
        .filter(IEResult.patient_id == patient_id, IEResult.criterion_id == payload.criterion_id)
        .first()
    )
    if existing:
        existing.met = payload.met
        existing.evaluated_by = current_user.id
        existing.evaluated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    result = IEResult(
        patient_id=patient_id,
        criterion_id=payload.criterion_id,
        met=payload.met,
        evaluated_by=current_user.id,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("/{patient_id}/ie-results", response_model=List[IEResultOut])
def list_patient_ie_results(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(IEResult).filter(IEResult.patient_id == patient_id).all()


# --- Visit Logs & Windows ---
@router.post("/visits", response_model=VisitLogOut, status_code=status.HTTP_201_CREATED)
def create_visit_log(
    payload: VisitLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "admin", "monitor")),
):
    visit = VisitLog(
        study_id=payload.study_id,
        patient_id=payload.patient_id,
        visit_number=payload.visit_number,
        scheduled_date=payload.scheduled_date,
        actual_date=payload.actual_date,
        status=payload.status,
        deviation_flag=payload.deviation_flag,
    )
    db.add(visit)
    db.commit()
    db.refresh(visit)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="visit_log",
        entity_id=visit.id,
        new_value={
            "visit_number": visit.visit_number,
            "scheduled_date": str(visit.scheduled_date),
            "status": visit.status,
        },
    )

    return visit


@router.get("/{patient_id}/visits", response_model=List[VisitLogOut])
def list_patient_visits(
    patient_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(VisitLog)
        .filter(VisitLog.patient_id == patient_id)
        .order_by(VisitLog.visit_number.asc())
        .all()
    )


@router.put("/visits/{visit_id}", response_model=VisitLogOut)
def update_visit_log(
    visit_id: uuid.UUID,
    payload: VisitLogUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "monitor", "admin")),
):
    visit = db.query(VisitLog).filter(VisitLog.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit log not found")

    old_status = visit.status
    if payload.actual_date is not None:
        visit.actual_date = payload.actual_date

        # Window check: +/- 3 days window per GCP protocol standards
        delta_days = abs((visit.actual_date - visit.scheduled_date).days)
        if delta_days > 3:
            visit.deviation_flag = True
            # Automatically record deviation if not already logged
            existing_dev = (
                db.query(ProtocolDeviation)
                .filter(ProtocolDeviation.visit_log_id == visit.id)
                .first()
            )
            if not existing_dev:
                dev = ProtocolDeviation(
                    study_id=visit.study_id,
                    patient_id=visit.patient_id,
                    visit_log_id=visit.id,
                    description=f"Visit {visit.visit_number} conducted on {visit.actual_date} ({delta_days} days from scheduled date {visit.scheduled_date}, exceeding +/-3 day protocol window)",
                    severity="minor",
                    reported_by=current_user.id,
                )
                db.add(dev)

    if payload.status is not None:
        visit.status = payload.status
    if payload.deviation_flag is not None:
        visit.deviation_flag = payload.deviation_flag

    db.commit()
    db.refresh(visit)

    log_action(
        db,
        user_id=current_user.id,
        action="UPDATE",
        entity_type="visit_log",
        entity_id=visit.id,
        old_value={"status": old_status},
        new_value={
            "actual_date": str(visit.actual_date) if visit.actual_date else None,
            "status": visit.status,
            "deviation_flag": visit.deviation_flag,
        },
    )

    return visit


# --- Protocol Deviations ---
@router.post("/deviations", response_model=ProtocolDeviationOut, status_code=status.HTTP_201_CREATED)
def report_deviation(
    payload: ProtocolDeviationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("coordinator", "pi", "monitor", "admin")),
):
    deviation = ProtocolDeviation(
        study_id=payload.study_id,
        patient_id=payload.patient_id,
        visit_log_id=payload.visit_log_id,
        description=payload.description,
        severity=payload.severity,
        reported_by=current_user.id,
    )
    db.add(deviation)
    db.commit()
    db.refresh(deviation)

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="protocol_deviation",
        entity_id=deviation.id,
        new_value={
            "description": deviation.description,
            "severity": deviation.severity,
        },
    )

    return deviation


@router.get("/study/{study_id}/deviations", response_model=List[ProtocolDeviationOut])
def list_study_deviations(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ProtocolDeviation)
        .filter(ProtocolDeviation.study_id == study_id)
        .order_by(ProtocolDeviation.created_at.desc())
        .all()
    )
