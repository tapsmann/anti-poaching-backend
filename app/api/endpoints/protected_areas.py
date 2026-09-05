from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_ranger, require_admin
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
    center_point: Optional[dict] = None

    class Config:
        from_attributes = True

# --- GET Routes ---
@router.get("/", response_model=List[ProtectedAreaResponse])
def get_protected_areas(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(ProtectedArea)
    if is_active is not None:
        query = query.filter(ProtectedArea.is_active == is_active)
    areas = query.offset(skip).limit(limit).all()
    results = []
    for area in areas:
        from app.core.geo import latlng_from_geometry
        lat, lng = latlng_from_geometry(area.center_point) if hasattr(area, 'center_point') and area.center_point else (None, None)
        results.append(ProtectedAreaResponse(
            id=area.id,
            name=area.name,
            zone_type=area.zone_type,
            risk_level=area.risk_level,
            size_hectares=area.size_hectares,
            description=area.description,
            is_active=area.is_active,
            protected_since=area.protected_since if hasattr(area, 'protected_since') else None,
            created_at=area.created_at,
            updated_at=area.updated_at,
            center_point={"lat": lat, "lng": lng} if lat and lng else None,
        ))
    return results

@router.get("/{area_id}", response_model=ProtectedAreaResponse)
def get_protected_area_by_id(
    area_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    area = db.query(ProtectedArea).filter(ProtectedArea.id == area_id).first()
    if not area:
        raise HTTPException(status_code=404, detail="Protected area not found")
    from app.core.geo import latlng_from_geometry
    lat, lng = latlng_from_geometry(area.center_point) if hasattr(area, 'center_point') and area.center_point else (None, None)
    return ProtectedAreaResponse(
        id=area.id,
        name=area.name,
        zone_type=area.zone_type,
        risk_level=area.risk_level,
        size_hectares=area.size_hectares,
        description=area.description,
        is_active=area.is_active,
        protected_since=area.protected_since if hasattr(area, 'protected_since') else None,
        created_at=area.created_at,
        updated_at=area.updated_at,
        center_point={"lat": lat, "lng": lng} if lat and lng else None,
    )

# --- POST Routes ---
@router.post("/", response_model=ProtectedAreaResponse, status_code=201)
def create_protected_area(
    area: ProtectedAreaCreate,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
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
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
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
def delete_protected_area(
    area_id: int,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    db_area = db.query(ProtectedArea).filter(ProtectedArea.id == area_id).first()
    if not db_area:
        raise HTTPException(status_code=404, detail="Protected area not found")
    db.delete(db_area)
    db.commit()
