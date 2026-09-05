"""
Pydantic schemas for request/response bodies.

Drop in as app/schemas.py. Only auth-related schemas for now —
add more here as you build out /studies, /patients, /ae, etc.
"""

import uuid
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