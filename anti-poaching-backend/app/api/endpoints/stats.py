from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import get_current_ranger
from app.models.incident import Incident
from app.models.patrol import Patrol
from app.models.protected_area import ProtectedArea
from app.models.report import CommunityReport
from app.models.ranger import Ranger
from app.models.species import Species
from app.schemas.serializers import serialize_incident
from app.services.ml_service import generate_hotspots

router = APIRouter()


def _dashboard_payload(db: Session) -> dict:
    total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    active_reports = (
        db.query(func.count(CommunityReport.id))
        .filter(CommunityReport.status.in_(["pending", "investigating", "verified"]))
        .scalar()
        or 0
    )
    rangers_on_duty = db.query(func.count(Ranger.id)).filter(Ranger.is_on_duty.is_(True)).scalar() or 0
    species_count = db.query(func.count(Species.id)).scalar() or 0
    active_patrols = db.query(func.count(Patrol.id)).filter(Patrol.status == "active").scalar() or 0

    incidents_by_park = (
        db.query(ProtectedArea.name, func.count(Incident.id))
        .outerjoin(Incident, Incident.protected_area_id == ProtectedArea.id)
        .group_by(ProtectedArea.name)
        .all()
    )
    total_park_incidents = sum(c for _, c in incidents_by_park) or 1
    park_breakdown = [
        {
            "park": name,
            "count": count,
            "percentage": round((count / total_park_incidents) * 100, 1),
        }
        for name, count in incidents_by_park
    ]

    recent = (
        db.query(Incident)
        .order_by(Incident.timestamp.desc())
        .limit(5)
        .all()
    )

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    monthly = (
        db.query(func.date_trunc("month", Incident.timestamp), func.count(Incident.id))
        .filter(Incident.timestamp >= thirty_days_ago - timedelta(days=335))
        .group_by(func.date_trunc("month", Incident.timestamp))
        .order_by(func.date_trunc("month", Incident.timestamp))
        .all()
    )
    trends = [
        {"month": row[0].strftime("%b %Y") if row[0] else "Unknown", "count": row[1]}
        for row in monthly
    ]

    hotspots = generate_hotspots()[:10]

    return {
        "total_incidents": total_incidents,
        "active_reports": active_reports,
        "rangers_on_duty": rangers_on_duty,
        "species_protected": species_count,
        "active_patrols": active_patrols,
        "incidents_by_park": park_breakdown,
        "recent_incidents": [serialize_incident(i).model_dump() for i in recent],
        "poaching_trends": trends,
        "hotspots": hotspots,
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    return _dashboard_payload(db)


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    payload = _dashboard_payload(db)
    resolved = db.query(func.count(Incident.id)).filter(Incident.is_resolved.is_(True)).scalar() or 0
    total = payload["total_incidents"] or 1
    return {
        **payload,
        "resolution_rate": round((resolved / total) * 100, 1),
        "avg_response_time_mins": 18,
        "conviction_rate": 82,
    }


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            db = SessionLocal()
            try:
                payload = _dashboard_payload(db)
            finally:
                db.close()
            await websocket.send_json({"type": "stats_update", "data": payload})
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
