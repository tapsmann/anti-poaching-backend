from datetime import datetime
from typing import Optional

from app.core.geo import coords_from_linestring, latlng_from_geometry
from app.models.incident import Incident
from app.models.patrol import Patrol
from app.models.report import CommunityReport
from app.models.ranger import Ranger
from app.schemas.schemas import (
    IncidentResponse,
    PatrolResponse,
    PointSchema,
    ReportResponse,
    RangerResponse,
)


def serialize_ranger(ranger: Ranger) -> RangerResponse:
    lat, lng = latlng_from_geometry(ranger.current_location or ranger.base_location)
    return RangerResponse(
        id=ranger.id,
        name=ranger.name,
        badge_number=ranger.badge_number,
        email=ranger.email,
        phone=ranger.phone,
        rank=ranger.rank,
        specialization=ranger.specialization,
        is_active=ranger.is_active,
        is_on_duty=ranger.is_on_duty,
        latitude=lat,
        longitude=lng,
        hire_date=ranger.hire_date,
        created_at=ranger.created_at,
        updated_at=ranger.updated_at,
    )


def serialize_incident(incident: Incident) -> IncidentResponse:
    lat, lng = latlng_from_geometry(incident.location)
    species_name = incident.species.name if incident.species else None
    ranger_name = incident.ranger.name if incident.ranger else None
    area_name = incident.protected_area.name if incident.protected_area else None
    return IncidentResponse(
        id=incident.id,
        latitude=lat,
        longitude=lng,
        incident_type=incident.incident_type,
        severity=incident.severity,
        description=incident.description,
        risk_score=incident.risk_score or 0.0,
        verified=incident.verified or False,
        is_resolved=incident.is_resolved or False,
        species_id=incident.species_id,
        species_name=species_name,
        protected_area_id=incident.protected_area_id,
        protected_area_name=area_name,
        ranger_id=incident.ranger_id,
        ranger_name=ranger_name,
        timestamp=incident.timestamp,
        created_at=incident.created_at,
    )


def serialize_report(report: CommunityReport) -> ReportResponse:
    lat, lng = latlng_from_geometry(report.location)
    ranger_name = report.assigned_ranger.name if report.assigned_ranger else None
    return ReportResponse(
        id=report.id,
        latitude=lat,
        longitude=lng,
        description=report.description,
        reporter_phone=report.reporter_phone,
        reporter_email=report.reporter_email,
        is_anonymous=report.is_anonymous,
        report_type=report.report_type,
        risk_score=report.risk_score or 0.0,
        status=report.status,
        incident_id=report.incident_id,
        assigned_ranger_id=report.assigned_ranger_id,
        ranger_name=ranger_name,
        ranger_notes=report.ranger_notes,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def serialize_patrol(patrol: Patrol) -> PatrolResponse:
    route_coords = coords_from_linestring(patrol.route)
    route = [PointSchema(lat=c["lat"], lng=c["lng"]) for c in route_coords]
    return PatrolResponse(
        id=patrol.id,
        ranger_id=patrol.ranger_id,
        ranger_name=patrol.ranger.name if patrol.ranger else None,
        route=route,
        start_time=patrol.start_time,
        end_time=patrol.end_time,
        protected_area_id=patrol.protected_area_id,
        protected_area_name=patrol.protected_area.name if patrol.protected_area else None,
        patrol_type=patrol.patrol_type,
        objectives=patrol.objectives,
        area_covered_km2=patrol.area_covered_km2,
        status=patrol.status,
        notes=patrol.notes,
        created_at=patrol.created_at,
        updated_at=patrol.updated_at,
    )
