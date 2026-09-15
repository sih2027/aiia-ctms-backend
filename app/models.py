"""
SQLAlchemy ORM models for the AIIA CTMS backend (AAYUR SATHI).

Implements the 14-table locked schema from the Master Technical Specification:
- users
- research_study
- study_team
- patient
- informed_consent
- adverse_event
- visit_log
- data_query
- monitoring_visit
- ie_criteria
- ie_result
- protocol_deviation
- milestone
- audit_trail
- audit_anchor
- notifications
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
    UniqueConstraint,
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
    ayurvedic_intervention = Column(String(255))
    ayush_system = Column(String(50), default="Ayurveda")
    classical_reference = Column(String(255))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    principal_investigator = relationship("User", foreign_keys=[principal_investigator_id])
    team_members = relationship("StudyTeam", back_populates="study", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("enrolled_count <= enrollment_target", name="ck_research_study_enrollment"),
    )


class StudyTeam(Base):
    __tablename__ = "study_team"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    study = relationship("ResearchStudy", back_populates="team_members")
    user = relationship("User", foreign_keys=[user_id])
    assigner = relationship("User", foreign_keys=[assigned_by])

    __table_args__ = (
        CheckConstraint(
            "role IN ('pi', 'co_pi', 'coordinator', 'monitor', 'sub_investigator')",
            name="ck_study_team_role",
        ),
        UniqueConstraint("study_id", "user_id", "role", name="uq_study_team"),
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
    abha_id = Column(String(50))
    abha_status = Column(String(20), default="unverified")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    consents = relationship("InformedConsent", back_populates="patient", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "status IN ('screened','enrolled','completed','withdrawn','screen_failed')",
            name="ck_patient_status",
        ),
    )


class InformedConsent(Base):
    __tablename__ = "informed_consent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id", ondelete="CASCADE"), nullable=False)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id", ondelete="CASCADE"), nullable=False)
    consent_version = Column(String(50), nullable=False)
    consented_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    withdrawn_at = Column(DateTime(timezone=True))
    withdrawal_reason = Column(Text)
    consent_document_ref = Column(String(500))
    witnessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="consents")
    study = relationship("ResearchStudy")
    witness = relationship("User", foreign_keys=[witnessed_by])


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
    regulatory_deadline = Column(Date, nullable=False)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(30))
    ae_term = Column(String(255))
    causality = Column(String(30))
    action_taken = Column(Text)
    reporter_role = Column(String(50))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    patient = relationship("Patient")
    reporter = relationship("User", foreign_keys=[reported_by])

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


class DataQuery(Base):
    __tablename__ = "data_query"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id", ondelete="SET NULL"))
    visit_log_id = Column(UUID(as_uuid=True), ForeignKey("visit_log.id", ondelete="SET NULL"))
    raised_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    field_name = Column(String(100), nullable=False)
    query_text = Column(Text, nullable=False)
    resolution_text = Column(Text)
    status = Column(String(30), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True))

    study = relationship("ResearchStudy")
    patient = relationship("Patient")
    visit_log = relationship("VisitLog")
    raiser = relationship("User", foreign_keys=[raised_by])
    resolver = relationship("User", foreign_keys=[resolved_by])

    __table_args__ = (
        CheckConstraint("status IN ('open','answered','closed')", name="ck_data_query_status"),
    )


class MonitoringVisit(Base):
    __tablename__ = "monitoring_visit"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id", ondelete="CASCADE"), nullable=False)
    monitor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    visit_date = Column(Date, nullable=False)
    visit_type = Column(String(50), nullable=False)
    findings = Column(Text)
    issues_identified = Column(Text)
    follow_up_required = Column(Boolean, nullable=False, default=False)
    report_submitted_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")
    monitor = relationship("User", foreign_keys=[monitor_id])

    __table_args__ = (
        CheckConstraint(
            "visit_type IN ('initiation','routine','for_cause','close_out')",
            name="ck_monitoring_visit_type",
        ),
    )


class IECriteria(Base):
    __tablename__ = "ie_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_id = Column(UUID(as_uuid=True), ForeignKey("research_study.id", ondelete="CASCADE"), nullable=False)
    criterion_type = Column(String(20), nullable=False)
    criterion_number = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    study = relationship("ResearchStudy")

    __table_args__ = (
        CheckConstraint("criterion_type IN ('inclusion','exclusion')", name="ck_ie_criteria_type"),
        UniqueConstraint("study_id", "criterion_type", "criterion_number", name="uq_ie_criteria"),
    )


class IEResult(Base):
    __tablename__ = "ie_result"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patient.id", ondelete="CASCADE"), nullable=False)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("ie_criteria.id", ondelete="CASCADE"), nullable=False)
    met = Column(Boolean, nullable=False)
    evaluated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    evaluated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    patient = relationship("Patient")
    criterion = relationship("IECriteria")
    evaluator = relationship("User", foreign_keys=[evaluated_by])

    __table_args__ = (
        UniqueConstraint("patient_id", "criterion_id", name="uq_ie_result"),
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
    """
    __tablename__ = "audit_trail"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)
    entity_type = Column(String(60), nullable=False)
    entity_id = Column(UUID(as_uuid=True))
    old_value = Column(JSONB)
    new_value = Column(JSONB)
    row_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User")


class AuditAnchor(Base):
    """INSERT ONLY — blockchain commit ledger."""
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


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False, default="info")
    is_read = Column(Boolean, nullable=False, default=False)
    link = Column(String(255))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    user = relationship("User")

    __table_args__ = (
        CheckConstraint("severity IN ('info','warning','critical')", name="ck_notifications_severity"),
    )