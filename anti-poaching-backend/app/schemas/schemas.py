from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class RangerCreate(BaseModel):
    name: str
    email: EmailStr
    badge_number: str
    password: Optional[str] = None
    rank: Optional[str] = None
    specialization: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RangerResponse(BaseModel):
    id: int
    name: str
    email: str
    badge_number: str
    rank: Optional[str]
    specialization: Optional[str]
    is_active: bool
    is_on_duty: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Add missing schemas
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
