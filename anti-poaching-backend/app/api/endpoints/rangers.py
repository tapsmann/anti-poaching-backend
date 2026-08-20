from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_ranger
from app.models.ranger import Ranger
from app.schemas.schemas import RangerCreate, RangerResponse, RangerUpdate
from app.schemas.serializers import serialize_ranger
from app.core.geo import point_from_latlng
from app.core.security import get_password_hash

router = APIRouter()


@router.get("/", response_model=list[RangerResponse])
def get_rangers(
    skip: int = 0,
    limit: int = 100,
    is_active: bool | None = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(Ranger)
    if is_active is not None:
        query = query.filter(Ranger.is_active == is_active)
    return [serialize_ranger(r) for r in query.offset(skip).limit(limit).all()]


@router.get("/{ranger_id}", response_model=RangerResponse)
def get_ranger_by_id(
    ranger_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")
    return serialize_ranger(ranger)


@router.post("/", response_model=RangerResponse, status_code=201)
def create_ranger(
    ranger: RangerCreate,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    existing = db.query(Ranger).filter(
        (Ranger.badge_number == ranger.badge_number) | (Ranger.email == ranger.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ranger already exists")

    data = ranger.model_dump(exclude={"password", "latitude", "longitude"})
    db_ranger = Ranger(**data, password_hash=get_password_hash(ranger.password or "ranger123"))
    if ranger.latitude is not None and ranger.longitude is not None:
        loc = point_from_latlng(ranger.latitude, ranger.longitude)
        db_ranger.base_location = loc
        db_ranger.current_location = loc
    db.add(db_ranger)
    db.commit()
    db.refresh(db_ranger)
    return serialize_ranger(db_ranger)


@router.put("/{ranger_id}", response_model=RangerResponse)
def update_ranger(
    ranger_id: int,
    ranger: RangerUpdate,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not db_ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")

    for key, value in ranger.model_dump(exclude_unset=True, exclude={"password", "latitude", "longitude"}).items():
        setattr(db_ranger, key, value)
    if ranger.password:
        db_ranger.password_hash = get_password_hash(ranger.password)
    if ranger.latitude is not None and ranger.longitude is not None:
        loc = point_from_latlng(ranger.latitude, ranger.longitude)
        db_ranger.current_location = loc

    db.commit()
    db.refresh(db_ranger)
    return serialize_ranger(db_ranger)


@router.delete("/{ranger_id}", status_code=204)
def delete_ranger(
    ranger_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_ranger = db.query(Ranger).filter(Ranger.id == ranger_id).first()
    if not db_ranger:
        raise HTTPException(status_code=404, detail="Ranger not found")
    db.delete(db_ranger)
    db.commit()
