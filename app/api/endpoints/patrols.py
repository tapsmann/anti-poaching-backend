from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import linestring_from_coords, point_from_latlng
from app.core.security import get_current_ranger, require_admin, check_ranger_can_access_area
from app.models.patrol import Patrol
from app.models.ranger import Ranger
from app.schemas.schemas import PatrolCreate, PatrolResponse, PatrolUpdate
from app.schemas.serializers import serialize_patrol

router = APIRouter()


@router.get("/", response_model=list[PatrolResponse])
def get_patrols(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    ranger_id: int | None = None,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    query = db.query(Patrol)
    if current_ranger.role == "ranger":
        if current_ranger.assigned_area_id is None:
            return []
        query = query.filter(Patrol.protected_area_id == current_ranger.assigned_area_id)
    if status:
        query = query.filter(Patrol.status == status)
    if ranger_id:
        query = query.filter(Patrol.ranger_id == ranger_id)
    patrols = query.order_by(Patrol.start_time.desc()).offset(skip).limit(limit).all()
    return [serialize_patrol(p) for p in patrols]


@router.get("/{patrol_id}", response_model=PatrolResponse)
def get_patrol_by_id(
    patrol_id: int,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    patrol = db.query(Patrol).filter(Patrol.id == patrol_id).first()
    if not patrol:
        raise HTTPException(status_code=404, detail="Patrol not found")
    if current_ranger.role == "ranger":
        if not check_ranger_can_access_area(current_ranger, patrol.protected_area_id):
            raise HTTPException(status_code=403, detail="Access denied: patrol is in a different park")
    return serialize_patrol(patrol)


@router.post("/", response_model=PatrolResponse, status_code=201)
def create_patrol(
    patrol: PatrolCreate,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    if current_ranger.role == "ranger":
        if current_ranger.assigned_area_id is None:
            raise HTTPException(status_code=403, detail="No park assigned to this ranger")
        if patrol.protected_area_id and patrol.protected_area_id != current_ranger.assigned_area_id:
            raise HTTPException(status_code=403, detail="Access denied: cannot create patrols in a different park")
    db_patrol = Patrol(
        route=linestring_from_coords([c.model_dump() for c in patrol.route]) if patrol.route else None,
        ranger_id=patrol.ranger_id or current_ranger.id,
        start_time=patrol.start_time or datetime.utcnow(),
        end_time=patrol.end_time,
        protected_area_id=patrol.protected_area_id or current_ranger.assigned_area_id,
        patrol_type=patrol.patrol_type,
        objectives=patrol.objectives,
        area_covered_km2=patrol.area_covered_km2,
        status=patrol.status or "planned",
        notes=patrol.notes,
    )
    db.add(db_patrol)
    db.commit()
    db.refresh(db_patrol)
    return serialize_patrol(db_patrol)


@router.put("/{patrol_id}", response_model=PatrolResponse)
def update_patrol(
    patrol_id: int,
    patrol: PatrolUpdate,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    db_patrol = db.query(Patrol).filter(Patrol.id == patrol_id).first()
    if not db_patrol:
        raise HTTPException(status_code=404, detail="Patrol not found")
    if current_ranger.role == "ranger":
        if not check_ranger_can_access_area(current_ranger, db_patrol.protected_area_id):
            raise HTTPException(status_code=403, detail="Access denied: patrol is in a different park")

    for key, value in patrol.model_dump(exclude_unset=True, exclude={"route"}).items():
        setattr(db_patrol, key, value)
    if patrol.route:
        db_patrol.route = linestring_from_coords([c.model_dump() for c in patrol.route])

    db.commit()
    db.refresh(db_patrol)
    return serialize_patrol(db_patrol)


@router.post("/{patrol_id}/complete", response_model=PatrolResponse)
def complete_patrol(
    patrol_id: int,
    db: Session = Depends(get_db),
    current_ranger: Ranger = Depends(get_current_ranger),
):
    db_patrol = db.query(Patrol).filter(Patrol.id == patrol_id).first()
    if not db_patrol:
        raise HTTPException(status_code=404, detail="Patrol not found")
    if current_ranger.role == "ranger":
        if not check_ranger_can_access_area(current_ranger, db_patrol.protected_area_id):
            raise HTTPException(status_code=403, detail="Access denied: patrol is in a different park")
    db_patrol.status = "completed"
    db_patrol.end_time = datetime.utcnow()
    db.commit()
    db.refresh(db_patrol)
    return serialize_patrol(db_patrol)


@router.delete("/{patrol_id}", status_code=204)
def delete_patrol(
    patrol_id: int,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    db_patrol = db.query(Patrol).filter(Patrol.id == patrol_id).first()
    if not db_patrol:
        raise HTTPException(status_code=404, detail="Patrol not found")
    db.delete(db_patrol)
    db.commit()
