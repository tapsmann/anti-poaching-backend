from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.security import get_current_ranger, require_admin, require_supervisor_or_admin
from app.models.equipment import Equipment
from app.models.ranger import Ranger

router = APIRouter()


class EquipmentCreate(BaseModel):
    name: str
    type: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = "active"
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_to: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EquipmentResponse(BaseModel):
    id: int
    name: str
    type: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_to: Optional[int] = None
    assigned_to_name: Optional[str] = None
    status: Optional[str] = None
    purchase_date: Optional[datetime] = None
    last_maintenance: Optional[datetime] = None
    next_maintenance: Optional[datetime] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


def _serialize(eq: Equipment, db: Session) -> EquipmentResponse:
    assigned_name = None
    if eq.assigned_to:
        ranger = db.query(Ranger).filter(Ranger.id == eq.assigned_to).first()
        if ranger:
            assigned_name = ranger.name
    from app.core.geo import latlng_from_geometry
    lat, lng = latlng_from_geometry(eq.current_location or eq.last_known_location)
    return EquipmentResponse(
        id=eq.id, name=eq.name, type=eq.type, serial_number=eq.serial_number,
        assigned_to=eq.assigned_to, assigned_to_name=assigned_name, status=eq.status,
        purchase_date=eq.purchase_date, last_maintenance=eq.last_maintenance,
        next_maintenance=eq.next_maintenance, notes=eq.notes,
        latitude=lat, longitude=lng,
        created_at=eq.created_at, updated_at=eq.updated_at,
    )


@router.get("/", response_model=list[EquipmentResponse])
def get_equipment(
    skip: int = 0, limit: int = 100,
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(Equipment)
    if type:
        query = query.filter(Equipment.type == type)
    if status:
        query = query.filter(Equipment.status == status)
    return [_serialize(e, db) for e in query.offset(skip).limit(limit).all()]


@router.get("/{eq_id}", response_model=EquipmentResponse)
def get_equipment_by_id(eq_id: int, db: Session = Depends(get_db), _: Ranger = Depends(get_current_ranger)):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return _serialize(eq, db)


@router.post("/", response_model=EquipmentResponse, status_code=201)
def create_equipment(eq_in: EquipmentCreate, db: Session = Depends(get_db), admin: Ranger = Depends(require_supervisor_or_admin)):
    data = eq_in.model_dump(exclude={"latitude", "longitude"})
    eq = Equipment(**data)
    if eq_in.latitude is not None and eq_in.longitude is not None:
        eq.current_location = point_from_latlng(eq_in.latitude, eq_in.longitude)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return _serialize(eq, db)


@router.put("/{eq_id}", response_model=EquipmentResponse)
def update_equipment(eq_id: int, eq_in: EquipmentUpdate, db: Session = Depends(get_db), admin: Ranger = Depends(require_supervisor_or_admin)):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    for key, value in eq_in.model_dump(exclude_unset=True, exclude={"latitude", "longitude"}).items():
        setattr(eq, key, value)
    if eq_in.latitude is not None and eq_in.longitude is not None:
        eq.current_location = point_from_latlng(eq_in.latitude, eq_in.longitude)
    db.commit()
    db.refresh(eq)
    return _serialize(eq, db)


@router.delete("/{eq_id}", status_code=204)
def delete_equipment(eq_id: int, db: Session = Depends(get_db), admin: Ranger = Depends(require_admin)):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")
    db.delete(eq)
    db.commit()
