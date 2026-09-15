"""
/studies routes — Chunk 1 (Study Tracker + KPIs), RBAC multi-investigator scoping,
and study team management per Master Technical Specification.
"""

import uuid
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit_log import log_action
from app.database import get_db
from app.models import Milestone, ResearchStudy, StudyTeam, User
from app.routers.auth import get_current_user, require_role
from app.schemas import (
    CtriRegister,
    IecDecision,
    MilestoneOut,
    StudyCreate,
    StudyDetailOut,
    StudyOut,
    StudyTeamAssign,
    StudyTeamOut,
)

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
        ctri_status=study.ctri_status or "not_registered",
        iec_approval_status=study.iec_approval_status or "pending",
        iec_approval_date=study.iec_approval_date,
        iec_renewal_due=study.iec_renewal_due,
        enrollment_target=study.enrollment_target,
        enrolled_count=study.enrolled_count,
        enrollment_percent=_enrollment_percent(study),
        site_id=study.site_id,
        principal_investigator_id=study.principal_investigator_id,
        start_date=study.start_date,
        end_date=study.end_date,
        ayurvedic_intervention=study.ayurvedic_intervention,
        ayush_system=study.ayush_system or "Ayurveda",
        classical_reference=study.classical_reference,
    )


@router.get("", response_model=List[StudyOut])
def list_studies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ResearchStudy)

    # Scoped study visibility per RBAC rules in Master Specification Section 4
    if current_user.role == "pi":
        # PI sees studies where they are primary PI OR assigned in study_team as pi/co_pi
        team_study_ids = [
            r[0]
            for r in db.query(StudyTeam.study_id)
            .filter(StudyTeam.user_id == current_user.id, StudyTeam.role.in_(["pi", "co_pi"]))
            .all()
        ]
        query = query.filter(
            or_(
                ResearchStudy.principal_investigator_id == current_user.id,
                ResearchStudy.id.in_(team_study_ids),
            )
        )
    elif current_user.role == "coordinator":
        # Coordinator sees studies they are assigned to
        coord_study_ids = [
            r[0]
            for r in db.query(StudyTeam.study_id)
            .filter(StudyTeam.user_id == current_user.id, StudyTeam.role == "coordinator")
            .all()
        ]
        if coord_study_ids:
            query = query.filter(ResearchStudy.id.in_(coord_study_ids))
        # If no explicit assignment yet, allow all for demo backwards compatibility
    elif current_user.role == "monitor":
        # Monitor sees studies they are assigned to
        mon_study_ids = [
            r[0]
            for r in db.query(StudyTeam.study_id)
            .filter(StudyTeam.user_id == current_user.id, StudyTeam.role == "monitor")
            .all()
        ]
        if mon_study_ids:
            query = query.filter(ResearchStudy.id.in_(mon_study_ids))
    # admin, ethics_committee, pharmacovigilance, regulator see all studies

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

    if current_user.role == "pi":
        is_assigned = (
            db.query(StudyTeam)
            .filter(
                StudyTeam.study_id == study_id,
                StudyTeam.user_id == current_user.id,
                StudyTeam.role.in_(["pi", "co_pi"]),
            )
            .first()
            is not None
        )
        if study.principal_investigator_id != current_user.id and not is_assigned:
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

    # Fetch study team
    team_rows = (
        db.query(StudyTeam, User)
        .join(User, StudyTeam.user_id == User.id)
        .filter(StudyTeam.study_id == study.id)
        .all()
    )
    team_outs = [
        StudyTeamOut(
            id=st.id,
            study_id=st.study_id,
            user_id=st.user_id,
            user_name=u.name,
            user_email=u.email,
            role=st.role,
            assigned_at=st.assigned_at,
        )
        for st, u in team_rows
    ]

    return StudyDetailOut(
        **_to_study_out(study).model_dump(),
        milestones=milestone_outs,
        overdue_milestone_count=overdue_count,
        team_members=team_outs,
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
        status="pending_iec",
        phase=payload.phase,
        sponsor=payload.sponsor,
        ctri_registration_number=payload.ctri_registration_number,
        enrollment_target=payload.enrollment_target,
        enrolled_count=0,
        site_id=payload.site_id,
        principal_investigator_id=pi_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        ayurvedic_intervention=payload.ayurvedic_intervention,
        ayush_system=payload.ayush_system or "Ayurveda",
        classical_reference=payload.classical_reference,
    )
    db.add(study)
    db.commit()
    db.refresh(study)

    # Automatically add the PI to the study_team
    db.add(
        StudyTeam(
            study_id=study.id,
            user_id=pi_id,
            role="pi",
            assigned_by=current_user.id,
        )
    )
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="CREATE",
        entity_type="research_study",
        entity_id=study.id,
        new_value={"title": study.title, "enrollment_target": study.enrollment_target},
    )

    return _to_study_out(study)


@router.post("/{study_id}/team", response_model=StudyTeamOut)
def assign_study_team_member(
    study_id: uuid.UUID,
    payload: StudyTeamAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pi")),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    if current_user.role == "pi" and study.principal_investigator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only lead PI or Admin can assign team members")

    user_to_assign = db.query(User).filter(User.id == payload.user_id).first()
    if not user_to_assign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already assigned with this role
    existing = (
        db.query(StudyTeam)
        .filter(StudyTeam.study_id == study_id, StudyTeam.user_id == payload.user_id, StudyTeam.role == payload.role)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has this role in this study")

    team_entry = StudyTeam(
        study_id=study_id,
        user_id=payload.user_id,
        role=payload.role,
        assigned_by=current_user.id,
    )
    db.add(team_entry)
    db.commit()
    db.refresh(team_entry)

    log_action(
        db,
        user_id=current_user.id,
        action="STUDY_TEAM_ASSIGN",
        entity_type="study_team",
        entity_id=team_entry.id,
        new_value={"study_id": str(study_id), "user_id": str(payload.user_id), "role": payload.role},
    )

    return StudyTeamOut(
        id=team_entry.id,
        study_id=team_entry.study_id,
        user_id=team_entry.user_id,
        user_name=user_to_assign.name,
        user_email=user_to_assign.email,
        role=team_entry.role,
        assigned_at=team_entry.assigned_at,
    )


@router.get("/{study_id}/team", response_model=List[StudyTeamOut])
def get_study_team(
    study_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if not study:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    team_rows = (
        db.query(StudyTeam, User)
        .join(User, StudyTeam.user_id == User.id)
        .filter(StudyTeam.study_id == study_id)
        .all()
    )
    return [
        StudyTeamOut(
            id=st.id,
            study_id=st.study_id,
            user_id=st.user_id,
            user_name=u.name,
            user_email=u.email,
            role=st.role,
            assigned_at=st.assigned_at,
        )
        for st, u in team_rows
    ]


@router.delete("/{study_id}/team/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_study_team_member(
    study_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pi")),
):
    team_entry = (
        db.query(StudyTeam)
        .filter(StudyTeam.study_id == study_id, StudyTeam.user_id == user_id)
        .first()
    )
    if not team_entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    db.delete(team_entry)
    db.commit()

    log_action(
        db,
        user_id=current_user.id,
        action="STUDY_TEAM_REMOVE",
        entity_type="study_team",
        entity_id=team_entry.id,
        old_value={"study_id": str(study_id), "user_id": str(user_id)},
    )
    return None


@router.post("/{study_id}/iec-decision", response_model=StudyOut)
def record_iec_decision(
    study_id: uuid.UUID,
    payload: IecDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("ethics_committee", "admin")),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    decision_norm = payload.decision.lower().strip()
    if decision_norm not in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'approved' or 'rejected'",
        )

    old_status = study.status
    old_iec = study.iec_approval_status
    today = date.today()

    if decision_norm == "approved":
        study.status = "iec_approved"
        study.iec_approval_status = "approved"
        study.iec_approval_date = today
        study.iec_renewal_due = today + timedelta(days=365)
        study.ctri_status = "pending"

        # Update or create IEC milestone
        iec_milestone = (
            db.query(Milestone)
            .filter(Milestone.study_id == study.id, Milestone.milestone_type == "iec_approval")
            .first()
        )
        if iec_milestone:
            iec_milestone.status = "completed"
            iec_milestone.completed_date = today
        else:
            db.add(
                Milestone(
                    study_id=study.id,
                    milestone_type="iec_approval",
                    due_date=today,
                    completed_date=today,
                    status="completed",
                )
            )

        # Add pending CTRI milestone if not already present
        ctri_milestone = (
            db.query(Milestone)
            .filter(Milestone.study_id == study.id, Milestone.milestone_type == "ctri_registration")
            .first()
        )
        if not ctri_milestone:
            db.add(
                Milestone(
                    study_id=study.id,
                    milestone_type="ctri_registration",
                    due_date=today + timedelta(days=15),
                    status="pending",
                )
            )

        action_type = "IEC_APPROVAL"
    else:
        study.status = "iec_rejected"
        study.iec_approval_status = "rejected"
        action_type = "IEC_REJECTION"

    db.commit()
    db.refresh(study)

    log_action(
        db,
        user_id=current_user.id,
        action=action_type,
        entity_type="research_study",
        entity_id=study.id,
        old_value={"status": old_status, "iec_approval_status": old_iec},
        new_value={
            "status": study.status,
            "iec_approval_status": study.iec_approval_status,
            "comments": payload.comments,
        },
    )

    return _to_study_out(study)


@router.post("/{study_id}/ctri-register", response_model=StudyOut)
def register_ctri(
    study_id: uuid.UUID,
    payload: CtriRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "pi")),
):
    study = db.query(ResearchStudy).filter(ResearchStudy.id == study_id).first()
    if study is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Study not found")

    if study.iec_approval_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study must have Institutional Ethics Committee (IEC) approval before CTRI registration",
        )

    today = date.today()
    reg_num = payload.ctri_registration_number
    if not reg_num:
        import random
        reg_num = f"CTRI/{today.year}/{today.month:02d}/0{random.randint(50000, 99999)}"

    old_status = study.status
    old_ctri = study.ctri_status

    study.ctri_registration_number = reg_num
    study.ctri_status = "registered"
    study.status = "site_activation"

    # Complete CTRI milestone
    ctri_milestone = (
        db.query(Milestone)
        .filter(Milestone.study_id == study.id, Milestone.milestone_type == "ctri_registration")
        .first()
    )
    if ctri_milestone:
        ctri_milestone.status = "completed"
        ctri_milestone.completed_date = today
    else:
        db.add(
            Milestone(
                study_id=study.id,
                milestone_type="ctri_registration",
                due_date=today,
                completed_date=today,
                status="completed",
            )
        )

    # Add site activation milestone if absent
    site_milestone = (
        db.query(Milestone)
        .filter(Milestone.study_id == study.id, Milestone.milestone_type == "site_activation")
        .first()
    )
    if not site_milestone:
        db.add(
            Milestone(
                study_id=study.id,
                milestone_type="site_activation",
                due_date=today + timedelta(days=7),
                status="pending",
            )
        )

    db.commit()
    db.refresh(study)

    log_action(
        db,
        user_id=current_user.id,
        action="CTRI_REGISTRATION",
        entity_type="research_study",
        entity_id=study.id,
        old_value={"status": old_status, "ctri_status": old_ctri},
        new_value={
            "status": study.status,
            "ctri_status": study.ctri_status,
            "ctri_registration_number": study.ctri_registration_number,
        },
    )

    return _to_study_out(study)
