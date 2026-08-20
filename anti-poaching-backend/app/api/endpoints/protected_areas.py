from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_ranger
from app.models.protected_area import ProtectedArea
from app.models.ranger import Ranger
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# --- Pydantic Schemas ---
class ProtectedAreaCreate(BaseModel):
    name: str
    zone_type: Optional[str] = None
    risk_level: Optional[str] = None
    size_hectares: Optional[float] = None
    description: Optional[str] = None

class ProtectedAreaUpdate(BaseModel):
    name: Optional[str] = None
    zone_type: Optional[str] = None
    risk_level: Optional[str] = None
    size_hectares: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProtectedAreaResponse(BaseModel):
    id: int
    name: str
    zone_type: Optional[str]
    risk_level: Optional[str]
    size_hectares: Optional[float]
    description: Optional[str]
    is_active: bool
    protected_since: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# --- GET Routes ---
@router.get("/", response_model=List[ProtectedAreaResponse])
def get_protected_areas(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all protected areas with optional filtering"""
    query = db.query(ProtectedArea)
    if is_active is not None:
        query = query.filter(ProtectedArea.is_active == is_active)
    areas = query.offset(skip).limit(limit).all()
    return areas

@router.get("/{area_id}", response_model=ProtectedAreaResponse)
def get_protected_area_by_id(area_id: int, db: Session = Depends(get_db)):
    """Get a single protected area by ID"""
    area = db.query(ProtectedArea).filter(ProtectedArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Protected area not found")
    return area

# --- POST Routes ---
@router.post("/", response_model=ProtectedAreaResponse, status_code=201)
def create_protected_area(
    area: ProtectedAreaCreate,
    db: Session = Depends(get_db)
):
    """Create a new protected area"""
    db_area = ProtectedArea(**area.model_dump())
    db.add(db_area)
    db.commit()
    db.refresh(db_area)
    return db_area

# --- PUT Routes ---
@router.put("/{area_id}", response_model=ProtectedAreaResponse)
def update_protected_area(
    area_id: int,
    area: ProtectedAreaUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing protected area"""
    db_area = db.query(ProtectedArea).filter(ProtectedArea.id == area_id).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Protected area not found")
    
    for key, value in area.model_dump(exclude_unset=True).items():
        setattr(db_area, key, value)
    
    db.commit()
    db.refresh(db_area)
    return db_area

# --- DELETE Routes ---
@router.delete("/{area_id}", status_code=204)
def delete_protected_area(area_id: int, db: Session = Depends(get_db)):
    """Delete a protected area"""
    db_area = db.query(ProtectedArea).filter(ProtectedArea.id == area_id).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Protected area not found")
    db.delete(db_area)
    db.commit()
    return {"message": "Protected area deleted successfully"}