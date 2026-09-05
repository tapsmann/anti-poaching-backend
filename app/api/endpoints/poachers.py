from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng, latlng_from_geometry
from app.core.security import get_current_ranger, require_admin, require_supervisor_or_admin
from app.models.poacher import Poacher
from app.models.ranger import Ranger

router = APIRouter()


class PoacherCreate(BaseModel):
    alias: Optional[str] = None
    description: Optional[str] = None
    known_affiliate: Optional[str] = None
    threat_level: Optional[str] = "medium"
    methods_used: Optional[str] = None
    target_species: Optional[str] = None
    estimated_age: Optional[int] = None
    nationality: Optional[str] = None
    identifying_marks: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PoacherUpdate(BaseModel):
    alias: Optional[str] = None
    description: Optional[str] = None
    known_affiliate: Optional[str] = None
    threat_level: Optional[str] = None
    methods_used: Optional[str] = None
    target_species: Optional[str] = None
    estimated_age: Optional[int] = None
    nationality: Optional[str] = None
    identifying_marks: Optional[str] = None
    is_captured: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class PoacherResponse(BaseModel):
    id: int
    alias: Optional[str] = None
    description: Optional[str] = None
    known_affiliate: Optional[str] = None
    threat_level: Optional[str] = None
    methods_used: Optional[str] = None
    target_species: Optional[str] = None
    estimated_age: Optional[int] = None
    nationality: Optional[str] = None
    identifying_marks: Optional[str] = None
    is_captured: bool = False
    captured_date: Optional[datetime] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


def _serialize(p: Poacher) -> PoacherResponse:
    lat, lng = latlng_from_geometry(p.last_known_location)
    return PoacherResponse(
        id=p.id, alias=p.alias, description=p.description,
        known_affiliate=p.known_affiliate, threat_level=p.threat_level,
        methods_used=p.methods_used, target_species=p.target_species,
        estimated_age=p.estimated_age, nationality=p.nationality,
        identifying_marks=p.identifying_marks, is_captured=p.is_captured,
        captured_date=p.captured_date, latitude=lat, longitude=lng,
        last_seen=p.last_seen, created_at=p.created_at, updated_at=p.updated_at,
    )


@router.get("/", response_model=list[PoacherResponse])
def get_poachers(
    skip: int = 0, limit: int = 100,
    threat_level: Optional[str] = None,
    is_captured: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(Poacher)
    if threat_level:
        query = query.filter(Poacher.threat_level == threat_level)
    if is_captured is not None:
        query = query.filter(Poacher.is_captured == is_captured)
    return [_serialize(p) for p in query.order_by(Poacher.created_at.desc()).offset(skip).limit(limit).all()]


@router.get("/{poacher_id}", response_model=PoacherResponse)
def get_poacher(poacher_id: int, db: Session = Depends(get_db), _: Ranger = Depends(get_current_ranger)):
    p = db.query(Poacher).filter(Poacher.id == poacher_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Poacher not found")
    return _serialize(p)


@router.post("/", response_model=PoacherResponse, status_code=201)
def create_poacher(poacher_in: PoacherCreate, db: Session = Depends(get_db), _: Ranger = Depends(get_current_ranger)):
    data = poacher_in.model_dump(exclude={"latitude", "longitude"})
    p = Poacher(**data)
    if poacher_in.latitude is not None and poacher_in.longitude is not None:
        p.last_known_location = point_from_latlng(poacher_in.latitude, poacher_in.longitude)
        p.last_seen = datetime.utcnow()
    db.add(p)
    db.commit()
    db.refresh(p)
    return _serialize(p)


@router.put("/{poacher_id}", response_model=PoacherResponse)
def update_poacher(poacher_id: int, poacher_in: PoacherUpdate, db: Session = Depends(get_db), __: Ranger = Depends(require_supervisor_or_admin)):
    p = db.query(Poacher).filter(Poacher.id == poacher_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Poacher not found")
    for key, value in poacher_in.model_dump(exclude_unset=True, exclude={"latitude", "longitude"}).items():
        setattr(p, key, value)
    if poacher_in.latitude is not None and poacher_in.longitude is not None:
        p.last_known_location = point_from_latlng(poacher_in.latitude, poacher_in.longitude)
        p.last_seen = datetime.utcnow()
    db.commit()
    db.refresh(p)
    return _serialize(p)


@router.delete("/{poacher_id}", status_code=204)
def delete_poacher(poacher_id: int, db: Session = Depends(get_db), __: Ranger = Depends(require_admin)):
    p = db.query(Poacher).filter(Poacher.id == poacher_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Poacher not found")
    db.delete(p)
    db.commit()
