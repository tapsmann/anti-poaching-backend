from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.security import check_ranger_can_access_area, get_current_ranger
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.ranger import Ranger

router = APIRouter()


class AlertCreate(BaseModel):
    incident_id: Optional[int] = None
    alert_type: str
    priority: Optional[str] = "medium"
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None


class AlertResponse(BaseModel):
    id: int
    incident_id: Optional[int] = None
    alert_type: str
    priority: Optional[str] = None
    message: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    status: str = "new"
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


def _serialize(alert: Alert) -> AlertResponse:
    from app.core.geo import latlng_from_geometry
    lat, lng = latlng_from_geometry(alert.location)
    return AlertResponse(
        id=alert.id, incident_id=alert.incident_id, alert_type=alert.alert_type,
        priority=alert.priority, message=alert.message, latitude=lat, longitude=lng,
        radius_km=alert.radius_km, status=alert.status, sent_at=alert.sent_at,
        created_at=alert.created_at,
    )


@router.get("/", response_model=list[AlertResponse])
def get_alerts(
    skip: int = 0, limit: int = 50,
    status: Optional[str] = None,
    alert_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    query = db.query(Alert)
    if current_ranger.role == "ranger":
        if current_ranger.assigned_area_id is None:
            return []
        query = query.join(Incident, Alert.incident_id == Incident.id).filter(
            Incident.protected_area_id == current_ranger.assigned_area_id
        )
    if status:
        query = query.filter(Alert.status == status)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    return [_serialize(a) for a in query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()]


@router.post("/", response_model=AlertResponse, status_code=201)
def create_alert(alert_in: AlertCreate, db: Session = Depends(get_db), current_ranger: Ranger = Depends(get_current_ranger)):
    if current_ranger.role == "ranger":
        if alert_in.incident_id is None:
            raise HTTPException(status_code=403, detail="Alerts must be linked to an incident in your park")
        incident = db.query(Incident).filter(Incident.id == alert_in.incident_id).first()
        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        if not check_ranger_can_access_area(current_ranger, incident.protected_area_id):
            raise HTTPException(status_code=403, detail="Access denied: incident is in a different park")
    alert = Alert(
        incident_id=alert_in.incident_id,
        alert_type=alert_in.alert_type,
        priority=alert_in.priority,
        message=alert_in.message,
        status="new",
        sent_at=datetime.utcnow(),
    )
    if alert_in.latitude is not None and alert_in.longitude is not None:
        alert.location = point_from_latlng(alert_in.latitude, alert_in.longitude)
    alert.radius_km = alert_in.radius_km
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return _serialize(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), current_ranger: Ranger = Depends(get_current_ranger)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if current_ranger.role == "ranger":
        if alert.incident_id is None:
            raise HTTPException(status_code=403, detail="Access denied: alert is not linked to your park")
        incident = db.query(Incident).filter(Incident.id == alert.incident_id).first()
        if not incident or not check_ranger_can_access_area(current_ranger, incident.protected_area_id):
            raise HTTPException(status_code=403, detail="Access denied: alert is in a different park")
    alert.status = "acknowledged"
    db.commit()
    db.refresh(alert)
    return _serialize(alert)
