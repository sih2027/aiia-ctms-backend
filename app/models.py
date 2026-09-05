"""
SQLAlchemy ORM models for the AIIA CTMS backend.

Mirrors the locked schema in Section 7 of the master context doc,
1:1 — table names, column names, types, and CHECK constraints match
database/schema.sql exactly. If you ever change one, change the other.

Drop this in as app/models.py. It imports Base from app.database,
which should already exist per Section 18.2.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Boolean,
    Text,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "role IN ('pi','coordinator','monitor','ethics_committee',"
            "'pharmacovigilance','admin','regulator')",
            name="ck_users_role",
        ),
    )


class ResearchStudy(Base):
    __tablename__ = "research_study"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False)
    phase = Column(String(50))
    sponsor = Column(String(255))
    ctri_registration_number = Column(String(100))
    ctri_status = Column(String(50), default="not_registered")
    iec_approval_status = Column(String(50), default="pending")
    iec_approval_date = Column(Date)
    iec_renewal_due = Column(Date)
    enrollment_target = Column(Integer, nullable=False)
    enrolled_count = Column(Integer, nullable=False, default=0)
    site_id = Column(String(100))
    principal_investigator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    principal_investigator = relationship("User")

    __table_args__ = (
        CheckConstraint("enrolled_count <= enrollment_target", name="ck_research_study_enrollment"),
    )


class Patient(Base):
    __tablename__ = "patient"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id"), nullable=False)
    screening_number = Column(String(50), nullable=False)
    randomization_number = Column(String(50))
    enrollment_date = Column(Date)
    status = Column(String(50))
    age = Column(Integer)
    sex = Column(String(10))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")

    __table_args__ = (
        CheckConstraint(
            "status IN ('screened','enrolled','completed','withdrawn','screen_failed')",
            name="ck_patient_status",
        ),
    )


class AdverseEvent(Base):
    __tablename__ = "adverse_event"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False)
    description = Column(Text, nullable=False)
    seriousness = Column(String(20))
    outcome = Column(String(100))
    onset_date = Column(Date)
    report_date = Column(Date, nullable=False)
    # Computed in FastAPI before INSERT (serious=+15d, non_serious=+30d) — NOT a DB trigger.
    regulatory_deadline = Column(Date, nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(30))
    ae_term = Column(String(255))  # synthetic MedDRA stub
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    patient = relationship("Patient")
    reporter = relationship("User")

    __table_args__ = (
        CheckConstraint("seriousness IN ('serious','non_serious')", name="ck_ae_seriousness"),
        CheckConstraint("regulatory_deadline > report_date", name="ck_ae_deadline_after_report"),
        CheckConstraint(
            "status IN ('open','under_review','resolved','reported')", name="ck_ae_status"
        ),
    )


class VisitLog(Base):
    __tablename__ = "visit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False)
    visit_number = Column(Integer, nullable=False)
    scheduled_date = Column(Date, nullable=False)
    actual_date = Column(Date)
    status = Column(String(30))
    deviation_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    patient = relationship("Patient")

    __table_args__ = (
        CheckConstraint(
            "status IN ('scheduled','completed','missed','overdue')", name="ck_visit_log_status"
        ),
    )


class ProtocolDeviation(Base):
    __tablename__ = "protocol_deviation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id"), nullable=False)
    visit_log_id = Column(UUID(as_uuid=True), ForeignKey("visit_log.id"))
    description = Column(Text, nullable=False)
    severity = Column(String(20))
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    patient = relationship("Patient")
    visit_log = relationship("VisitLog")
    reporter = relationship("User")

    __table_args__ = (
        CheckConstraint("severity IN ('minor','major','critical')", name="ck_deviation_severity"),
    )


class Milestone(Base):
    __tablename__ = "milestone"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id"), nullable=False)
    milestone_type = Column(String(60))
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date)
    status = Column(String(20))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")

    __table_args__ = (
        CheckConstraint(
            "milestone_type IN ('iec_approval','ctri_registration','site_activation',"
            "'first_patient_enrolled','last_patient_enrolled','database_lock',"
            "'study_closeout','iec_renewal')",
            name="ck_milestone_type",
        ),
        CheckConstraint(
            "status IN ('pending','completed','overdue')", name="ck_milestone_status"
        ),
    )


class AuditTrail(Base):
    """
    INSERT ONLY — never UPDATE or DELETE.

    The database-level immutability trigger (prevent_audit_modification,
    per Section 7/database/schema.sql) is the real enforcement point.
    This model intentionally has no update-oriented helper methods —
    don't add any. row_hash = SHA-256 hex of the previous row's content;
    the very first row hashes SHA-256("GENESIS").
    """

    __tablename__ = "audit_trail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    # values: CREATE, UPDATE, DELETE_ATTEMPT, LOGIN, LOGOUT, STATUS_CHANGE, EXPORT, AE_REPORT
    entity_type = Column(String(60), nullable=False)
    # values: research_study, patient, adverse_event, visit_log, milestone, user
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    row_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User")


class AuditAnchor(Base):
    """INSERT ONLY — blockchain commit ledger. Same immutability trigger as audit_trail."""

    __tablename__ = "audit_anchor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_start_id = Column(UUID(as_uuid=True), ForeignKey("audit_trail.id"))
    batch_end_id = Column(UUID(as_uuid=True), ForeignKey("audit_trail.id"))
    row_count = Column(Integer, nullable=False)
    merkle_root = Column(String(64), nullable=False)
    chain = Column(String(50), nullable=False, default="polygon-amoy-testnet")
    tx_hash = Column(String(100))
    block_number = Column(BigInteger)
    committed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    verification_status = Column(String(20), default="pending")

    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('pending','matched','mismatched')",
            name="ck_audit_anchor_verification_status",
        ),
    )