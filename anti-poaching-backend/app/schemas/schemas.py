from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ============ Auth Schemas ============
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: str

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

# ============ Ranger Schemas ============
class RangerCreate(BaseModel):
    name: str
    email: EmailStr
    badge_number: str
    password: Optional[str] = None
    rank: Optional[str] = None
    specialization: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RangerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    badge_number: Optional[str] = None
    rank: Optional[str] = None
    specialization: Optional[str] = None
    is_active: Optional[bool] = None
    is_on_duty: Optional[bool] = None

class RangerResponse(BaseModel):
    id: int
    name: str
    badge_number: str
    email: str
    phone: Optional[str] = None
    rank: Optional[str] = None
    specialization: Optional[str] = None
    is_active: bool
    is_on_duty: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    hire_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============ Incident Schemas ============
class IncidentCreate(BaseModel):
    latitude: float
    longitude: float
    incident_type: str
    severity: str
    description: Optional[str] = None
    species_id: Optional[int] = None
    protected_area_id: Optional[int] = None
    ranger_id: Optional[int] = None
    poacher_count: Optional[int] = 0
    evidence_photo: Optional[str] = None

class IncidentUpdate(BaseModel):
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    risk_score: Optional[float] = None
    verified: Optional[bool] = None
    is_resolved: Optional[bool] = None
    ranger_id: Optional[int] = None

class IncidentResponse(BaseModel):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    incident_type: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    risk_score: float = 0.0
    verified: bool = False
    is_resolved: bool = False
    species_id: Optional[int] = None
    species_name: Optional[str] = None
    protected_area_id: Optional[int] = None
    protected_area_name: Optional[str] = None
    ranger_id: Optional[int] = None
    ranger_name: Optional[str] = None
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# ============ Report Schemas ============
class ReportCreate(BaseModel):
    latitude: float
    longitude: float
    description: str
    reporter_phone: Optional[str] = None
    reporter_email: Optional[str] = None
    is_anonymous: bool = True
    report_type: Optional[str] = None

class ReportUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    risk_score: Optional[float] = None
    assigned_ranger_id: Optional[int] = None
    ranger_notes: Optional[str] = None

class ReportResponse(BaseModel):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: str
    reporter_phone: Optional[str] = None
    reporter_email: Optional[str] = None
    is_anonymous: bool = True
    report_type: Optional[str] = None
    risk_score: float = 0.0
    status: str = "pending"
    incident_id: Optional[int] = None
    assigned_ranger_id: Optional[int] = None
    ranger_name: Optional[str] = None
    ranger_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# ============ Patrol Schemas ============
class PointSchema(BaseModel):
    lat: float
    lng: float

class PatrolCreate(BaseModel):
    ranger_id: int
    protected_area_id: Optional[int] = None
    patrol_type: str
    objectives: Optional[str] = None
    area_covered_km2: Optional[float] = None
    notes: Optional[str] = None

class PatrolUpdate(BaseModel):
    ranger_id: Optional[int] = None
    protected_area_id: Optional[int] = None
    patrol_type: Optional[str] = None
    objectives: Optional[str] = None
    area_covered_km2: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    end_time: Optional[datetime] = None

class PatrolResponse(BaseModel):
    id: int
    ranger_id: int
    ranger_name: Optional[str] = None
    route: List[PointSchema] = []
    start_time: datetime
    end_time: Optional[datetime] = None
    protected_area_id: Optional[int] = None
    protected_area_name: Optional[str] = None
    patrol_type: Optional[str] = None
    objectives: Optional[str] = None
    area_covered_km2: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
