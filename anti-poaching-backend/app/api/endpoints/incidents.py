from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.security import get_current_ranger
from app.models.incident import Incident
from app.models.ranger import Ranger
from app.schemas.schemas import IncidentCreate, IncidentResponse, IncidentUpdate
from app.schemas.serializers import serialize_incident
from app.services.ml_service import predict_risk_score

router = APIRouter()


@router.get("/", response_model=list[IncidentResponse])
def get_incidents(
    skip: int = 0,
    limit: int = 100,
    severity: str | None = None,
    incident_type: str | None = None,
    is_resolved: bool | None = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(Incident)
    if severity:
        query = query.filter(Incident.severity == severity)
    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)
    if is_resolved is not None:
        query = query.filter(Incident.is_resolved == is_resolved)
    incidents = query.order_by(Incident.timestamp.desc()).offset(skip).limit(limit).all()
    return [serialize_incident(i) for i in incidents]


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_by_id(
    incident_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return serialize_incident(incident)


@router.post("/", response_model=IncidentResponse, status_code=201)
def create_incident(
    incident: IncidentCreate,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    risk = predict_risk_score(incident.latitude, incident.longitude)
    db_incident = Incident(
        location=point_from_latlng(incident.latitude, incident.longitude),
        incident_type=incident.incident_type,
        description=incident.description,
        severity=incident.severity,
        species_id=incident.species_id,
        protected_area_id=incident.protected_area_id,
        ranger_id=incident.ranger_id or current_ranger.id,
        verified=incident.verified,
        is_resolved=incident.is_resolved,
        risk_score=risk,
        timestamp=datetime.utcnow(),
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return serialize_incident(db_incident)


@router.put("/{incident_id}", response_model=IncidentResponse)
def update_incident(
    incident_id: int,
    incident: IncidentUpdate,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    updates = incident.model_dump(exclude_unset=True, exclude={"latitude", "longitude"})
    for key, value in updates.items():
        setattr(db_incident, key, value)

    if incident.latitude is not None and incident.longitude is not None:
        db_incident.location = point_from_latlng(incident.latitude, incident.longitude)
        db_incident.risk_score = predict_risk_score(incident.latitude, incident.longitude)

    db.commit()
    db.refresh(db_incident)
    return serialize_incident(db_incident)


@router.post("/{incident_id}/resolve", response_model=IncidentResponse)
def resolve_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db_incident.is_resolved = True
    db_incident.verified = True
    db.commit()
    db.refresh(db_incident)
    return serialize_incident(db_incident)


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
def assign_incident(
    incident_id: int,
    ranger_id: int = Query(...),
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")
    db_incident.ranger_id = ranger_id
    db.commit()
    db.refresh(db_incident)
    return serialize_incident(db_incident)


@router.delete("/{incident_id}", status_code=204)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not db_incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    db.delete(db_incident)
    db.commit()
