from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.security import check_ranger_can_access_area, get_current_ranger
from app.models.observation import PatrolObservation
from app.models.patrol import Patrol
from app.models.ranger import Ranger

router = APIRouter()


class ObservationCreate(BaseModel):
    patrol_id: int
    incident_id: Optional[int] = None
    species_id: Optional[int] = None
    observation_type: str
    latitude: float
    longitude: float
    description: Optional[str] = None
    photo_url: Optional[str] = None
    animal_count: Optional[int] = None
    severity: Optional[str] = None


class ObservationResponse(BaseModel):
    id: int
    patrol_id: int
    incident_id: Optional[int] = None
    species_id: Optional[int] = None
    ranger_id: Optional[int] = None
    observation_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None
    animal_count: Optional[int] = None
    severity: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


def _serialize(obs: PatrolObservation) -> ObservationResponse:
    from app.core.geo import latlng_from_geometry
    lat, lng = latlng_from_geometry(obs.location)
    return ObservationResponse(
        id=obs.id, patrol_id=obs.patrol_id, incident_id=obs.incident_id,
        species_id=obs.species_id, ranger_id=obs.ranger_id,
        observation_type=obs.observation_type, latitude=lat, longitude=lng,
        timestamp=obs.timestamp, description=obs.description,
        photo_url=obs.photo_url, animal_count=obs.animal_count,
        severity=obs.severity, created_at=obs.created_at,
    )


@router.get("/", response_model=list[ObservationResponse])
def get_observations(
    skip: int = 0, limit: int = 100,
    patrol_id: Optional[int] = None,
    observation_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    query = db.query(PatrolObservation)
    if current_ranger.role == "ranger":
        if current_ranger.assigned_area_id is None:
            return []
        query = query.join(Patrol, PatrolObservation.patrol_id == Patrol.id).filter(
            Patrol.protected_area_id == current_ranger.assigned_area_id
        )
    if patrol_id:
        query = query.filter(PatrolObservation.patrol_id == patrol_id)
    if observation_type:
        query = query.filter(PatrolObservation.observation_type == observation_type)
    return [_serialize(o) for o in query.order_by(PatrolObservation.created_at.desc()).offset(skip).limit(limit).all()]


@router.post("/", response_model=ObservationResponse, status_code=201)
def create_observation(
    obs_in: ObservationCreate,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    patrol = db.query(Patrol).filter(Patrol.id == obs_in.patrol_id).first()
    if not patrol:
        raise HTTPException(status_code=404, detail="Patrol not found")
    if current_ranger.role == "ranger" and not check_ranger_can_access_area(
        current_ranger, patrol.protected_area_id
    ):
        raise HTTPException(status_code=403, detail="Access denied: patrol is in a different park")
    obs = PatrolObservation(
        patrol_id=obs_in.patrol_id,
        incident_id=obs_in.incident_id,
        species_id=obs_in.species_id,
        ranger_id=current_ranger.id,
        observation_type=obs_in.observation_type,
        location=point_from_latlng(obs_in.latitude, obs_in.longitude),
        description=obs_in.description,
        photo_url=obs_in.photo_url,
        animal_count=obs_in.animal_count,
        severity=obs_in.severity,
        timestamp=datetime.utcnow(),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return _serialize(obs)
