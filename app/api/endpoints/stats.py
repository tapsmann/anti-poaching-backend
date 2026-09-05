from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
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
from app.services.ml_service import generate_hotspots, generate_park_hotspots

router = APIRouter()


def _dashboard_payload(db: Session, park_name: str | None = None) -> dict:
    query_incidents = db.query(Incident)
    query_reports = db.query(CommunityReport)
    query_patrols = db.query(Patrol)

    if park_name:
        park = db.query(ProtectedArea).filter(ProtectedArea.name.ilike(f"%{park_name}%")).first()
        if park:
            query_incidents = query_incidents.filter(Incident.protected_area_id == park.id)
            query_reports = query_reports.filter(
                CommunityReport.assigned_ranger_id.in_(
                    db.query(Ranger.id).filter(Ranger.assigned_area_id == park.id)
                )
            )
            query_patrols = query_patrols.filter(Patrol.protected_area_id == park.id)

    total_incidents = query_incidents.count() or 0
    active_reports = (
        db.query(func.count(CommunityReport.id))
        .filter(CommunityReport.status.in_(["pending", "investigating", "verified"]))
        .scalar() or 0
    )
    rangers_on_duty = db.query(func.count(Ranger.id)).filter(Ranger.is_on_duty.is_(True)).scalar() or 0
    species_count = db.query(func.count(Species.id)).scalar() or 0
    active_patrols = query_patrols.filter(Patrol.status == "active").count() or 0

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
        query_incidents
        .order_by(Incident.timestamp.desc())
        .limit(8)
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

    type_counts = (
        query_incidents
        .with_entities(Incident.incident_type, func.count(Incident.id))
        .group_by(Incident.incident_type)
        .all()
    )
    by_type = [{"type": t.replace("_", " ").title(), "count": c} for t, c in type_counts]

    severity_counts = (
        query_incidents
        .with_entities(Incident.severity, func.count(Incident.id))
        .group_by(Incident.severity)
        .all()
    )
    by_severity = [{"severity": s, "count": c} for s, c in severity_counts]

    resolved_count = query_incidents.filter(Incident.is_resolved.is_(True)).count() or 0
    unresolved_count = total_incidents - resolved_count

    hotspots = generate_hotspots()[:12]

    return {
        "total_incidents": total_incidents,
        "active_reports": active_reports,
        "rangers_on_duty": rangers_on_duty,
        "species_protected": species_count,
        "active_patrols": active_patrols,
        "resolved_count": resolved_count,
        "unresolved_count": unresolved_count,
        "incidents_by_park": park_breakdown,
        "incidents_by_type": by_type,
        "incidents_by_severity": by_severity,
        "recent_incidents": [serialize_incident(i).model_dump() for i in recent],
        "poaching_trends": trends,
        "hotspots": hotspots,
        "updated_at": datetime.utcnow().isoformat(),
    }


def _enforce_park_scope(
    current_ranger: Ranger, park: str | None, db: Session
) -> str | None:
    if current_ranger.role in ("admin", "supervisor"):
        return park
    if current_ranger.assigned_area_id is None:
        raise HTTPException(status_code=403, detail="No park assigned to this ranger")
    assigned = db.query(ProtectedArea).filter(ProtectedArea.id == current_ranger.assigned_area_id).first()
    assigned_name = assigned.name if assigned else None
    if park:
        if assigned_name and park.lower() not in assigned_name.lower() and assigned_name.lower() not in park.lower():
            raise HTTPException(status_code=403, detail="Access denied: cannot view data from other parks")
        return park
    return assigned_name


@router.get("/dashboard")
def get_dashboard_stats(
    park: str | None = Query(None, description="Filter by park name"),
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    park = _enforce_park_scope(current_ranger, park, db)
    return _dashboard_payload(db, park_name=park)


@router.get("/analytics")
def get_analytics(
    park: str | None = Query(None),
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    park = _enforce_park_scope(current_ranger, park, db)
    payload = _dashboard_payload(db, park_name=park)
    resolved = payload.get("resolved_count", 0)
    total = payload["total_incidents"] or 1
    return {
        **payload,
        "resolution_rate": round((resolved / total) * 100, 1),
        "avg_response_time_mins": 18,
        "conviction_rate": 82,
        "patrol_coverage_km2": 847.5,
        "community_reports_this_month": payload["active_reports"],
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
