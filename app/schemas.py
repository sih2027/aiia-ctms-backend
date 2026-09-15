"""
Pydantic schemas for request/response bodies for AIIA CTMS (AAYUR SATHI).
"""

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True


# --- Study Schemas ---
class StudyCreate(BaseModel):
    title: str
    phase: Optional[str] = None
    sponsor: Optional[str] = None
    ctri_registration_number: Optional[str] = None
    enrollment_target: int
    site_id: Optional[str] = None
    principal_investigator_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    ayurvedic_intervention: Optional[str] = None
    ayush_system: Optional[str] = "Ayurveda"
    classical_reference: Optional[str] = None


class IecDecision(BaseModel):
    decision: str  # 'approved' or 'rejected'
    comments: Optional[str] = None


class CtriRegister(BaseModel):
    ctri_registration_number: Optional[str] = None


class StudyTeamAssign(BaseModel):
    user_id: uuid.UUID
    role: str  # 'pi', 'co_pi', 'coordinator', 'monitor', 'sub_investigator'


class StudyTeamOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    user_id: uuid.UUID
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    role: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class StudyOut(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    phase: Optional[str]
    sponsor: Optional[str]
    ctri_registration_number: Optional[str]
    ctri_status: str
    iec_approval_status: str
    iec_approval_date: Optional[date] = None
    iec_renewal_due: Optional[date] = None
    enrollment_target: int
    enrolled_count: int
    enrollment_percent: float
    site_id: Optional[str]
    principal_investigator_id: Optional[uuid.UUID]
    start_date: Optional[date]
    end_date: Optional[date]
    ayurvedic_intervention: Optional[str] = None
    ayush_system: Optional[str] = "Ayurveda"
    classical_reference: Optional[str] = None

    class Config:
        from_attributes = True


class MilestoneOut(BaseModel):
    id: uuid.UUID
    milestone_type: Optional[str]
    due_date: date
    completed_date: Optional[date]
    status: Optional[str]
    is_overdue: bool

    class Config:
        from_attributes = True


class StudyDetailOut(StudyOut):
    milestones: List[MilestoneOut]
    overdue_milestone_count: int
    team_members: Optional[List[StudyTeamOut]] = []


# --- Informed Consent (DPDP Act 2023 / Gate 2) ---
class ConsentRecordCreate(BaseModel):
    consent_version: str = "v1.0"
    consent_document_ref: Optional[str] = None
    witnessed_by: Optional[uuid.UUID] = None


class ConsentWithdraw(BaseModel):
    withdrawal_reason: str


class ConsentRecordOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    study_id: uuid.UUID
    consent_version: str
    consented_at: datetime
    withdrawn_at: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None
    consent_document_ref: Optional[str] = None
    witnessed_by: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


# --- Patient Schemas ---
class PatientScreen(BaseModel):
    study_id: uuid.UUID
    screening_number: str
    age: Optional[int] = None
    sex: Optional[str] = None
    abha_id: Optional[str] = None


class PatientEnroll(BaseModel):
    patient_id: uuid.UUID
    enrollment_date: Optional[date] = None
    randomization_number: Optional[str] = None


class PatientStatusUpdate(BaseModel):
    status: str  # screened, enrolled, completed, withdrawn, screen_failed
    reason: Optional[str] = None


class PatientOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    screening_number: str
    randomization_number: Optional[str] = None
    enrollment_date: Optional[date] = None
    status: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    abha_id: Optional[str] = None
    abha_status: Optional[str] = "unverified"
    has_valid_consent: bool = False

    class Config:
        from_attributes = True


# --- Inclusion / Exclusion Schemas ---
class IECriteriaCreate(BaseModel):
    criterion_type: str  # inclusion, exclusion
    criterion_number: int
    description: str


class IECriteriaOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    criterion_type: str
    criterion_number: int
    description: str

    class Config:
        from_attributes = True


class IEResultCreate(BaseModel):
    criterion_id: uuid.UUID
    met: bool


class IEResultOut(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    criterion_id: uuid.UUID
    met: bool
    evaluated_by: Optional[uuid.UUID] = None
    evaluated_at: datetime

    class Config:
        from_attributes = True


# --- Visit Log Schemas ---
class VisitLogCreate(BaseModel):
    study_id: uuid.UUID
    patient_id: uuid.UUID
    visit_number: int
    scheduled_date: date
    actual_date: Optional[date] = None
    status: str = "scheduled"
    deviation_flag: bool = False


class VisitLogUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[str] = None
    deviation_flag: Optional[bool] = None


class VisitLogOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    patient_id: uuid.UUID
    visit_number: int
    scheduled_date: date
    actual_date: Optional[date] = None
    status: Optional[str] = None
    deviation_flag: bool = False

    class Config:
        from_attributes = True


# --- Protocol Deviation Schemas ---
class ProtocolDeviationCreate(BaseModel):
    study_id: uuid.UUID
    patient_id: uuid.UUID
    visit_log_id: Optional[uuid.UUID] = None
    description: str
    severity: str = "minor"  # minor, major, critical


class ProtocolDeviationOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    patient_id: uuid.UUID
    visit_log_id: Optional[uuid.UUID] = None
    description: str
    severity: Optional[str] = None
    reported_by: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Adverse Event Schemas ---
class AdverseEventCreate(BaseModel):
    study_id: uuid.UUID
    patient_id: uuid.UUID
    description: str
    seriousness: str  # serious, non_serious
    outcome: Optional[str] = "recovering"
    onset_date: Optional[date] = None
    report_date: Optional[date] = None  # defaults to today
    ae_term: Optional[str] = None
    causality: Optional[str] = None  # certain, probable, possible, unlikely, unclassified, unclassifiable
    action_taken: Optional[str] = None


class AdverseEventStatusUpdate(BaseModel):
    status: str  # open, under_review, resolved, reported
    outcome: Optional[str] = None


class WHOUMCCausalityUpdate(BaseModel):
    causality: str  # certain, probable, possible, unlikely, unclassified, unclassifiable
    action_taken: Optional[str] = None
    comments: Optional[str] = None


class AdverseEventOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    patient_id: uuid.UUID
    description: str
    seriousness: str
    outcome: Optional[str] = None
    onset_date: Optional[date] = None
    report_date: date
    regulatory_deadline: date
    reported_by: Optional[uuid.UUID] = None
    status: Optional[str] = None
    ae_term: Optional[str] = None
    causality: Optional[str] = None
    action_taken: Optional[str] = None
    is_overdue: bool = False

    class Config:
        from_attributes = True


class AESummaryOut(BaseModel):
    study_id: uuid.UUID
    total_ae_count: int
    serious_count: int
    non_serious_count: int
    overdue_count: int
    open_count: int
    resolved_count: int


class SafetySignalOut(BaseModel):
    study_id: uuid.UUID
    study_title: str
    ae_term: str
    count_in_30_days: int
    earliest_date: date
    latest_date: date
    signal_level: str  # HIGH, MEDIUM
    intervention: Optional[str] = None
    recommendation: str


# --- Data Query Engine (GCP Monitor) ---
class DataQueryCreate(BaseModel):
    study_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    visit_log_id: Optional[uuid.UUID] = None
    field_name: str
    query_text: str


class DataQueryAnswer(BaseModel):
    resolution_text: str


class DataQueryClose(BaseModel):
    comments: Optional[str] = None


class DataQueryOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    visit_log_id: Optional[uuid.UUID] = None
    raised_by: uuid.UUID
    raiser_name: Optional[str] = None
    resolved_by: Optional[uuid.UUID] = None
    resolver_name: Optional[str] = None
    field_name: str
    query_text: str
    resolution_text: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Monitoring Visits (ALCOA+) ---
class MonitoringVisitCreate(BaseModel):
    study_id: uuid.UUID
    visit_date: date
    visit_type: str  # initiation, routine, for_cause, close_out
    findings: Optional[str] = None
    issues_identified: Optional[str] = None
    follow_up_required: bool = False


class MonitoringVisitOut(BaseModel):
    id: uuid.UUID
    study_id: uuid.UUID
    monitor_id: uuid.UUID
    monitor_name: Optional[str] = None
    visit_date: date
    visit_type: str
    findings: Optional[str] = None
    issues_identified: Optional[str] = None
    follow_up_required: bool = False
    report_submitted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Notifications ---
class NotificationOut(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    severity: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- ABDM Sandbox Schemas ---
class ABDMVerifyIn(BaseModel):
    abha_id: str


class ABDMVerifyOut(BaseModel):
    abha_id: str
    status: str  # verified, invalid
    name: Optional[str] = None
    gender: Optional[str] = None
    year_of_birth: Optional[int] = None
    verification_source: str


class CareContextPushIn(BaseModel):
    patient_id: uuid.UUID
    visit_log_id: Optional[uuid.UUID] = None
    display_title: str
