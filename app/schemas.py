"""
Pydantic schemas for request/response bodies.

Drop in as app/schemas.py (replaces the existing one — auth schemas are
unchanged, only study/milestone schemas were added for /studies).
"""

import uuid
from datetime import date
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
        from_attributes = True  # lets .model_validate() read straight off the ORM User object


class StudyCreate(BaseModel):
    title: str
    phase: Optional[str] = None
    sponsor: Optional[str] = None
    ctri_registration_number: Optional[str] = None
    enrollment_target: int
    site_id: Optional[str] = None
    # Optional: admin creating on a PI's behalf must supply this;
    # a PI creating their own study can omit it (defaults to themselves).
    principal_investigator_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class StudyOut(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    phase: Optional[str]
    sponsor: Optional[str]
    ctri_registration_number: Optional[str]
    ctri_status: str
    iec_approval_status: str
    enrollment_target: int
    enrolled_count: int
    enrollment_percent: float
    site_id: Optional[str]
    principal_investigator_id: Optional[uuid.UUID]
    start_date: Optional[date]
    end_date: Optional[date]

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
