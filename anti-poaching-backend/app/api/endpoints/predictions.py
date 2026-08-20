from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_ranger
from app.models.ranger import Ranger
from app.schemas.schemas import HotspotResponse, PredictionResponse
from app.services.ml_service import generate_hotspots, predict_risk_score

router = APIRouter()

REGION_CENTERS = {
    "zimbabwe": {"lat": -19.0, "lng": 29.5},
    "kenya": {"lat": -1.0, "lng": 36.0},
}


@router.post("/predict", response_model=PredictionResponse)
def predict_risk(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    now = datetime.utcnow()
    risk_score = predict_risk_score(lat, lng, now)
    return PredictionResponse(lat=lat, lng=lng, risk_score=risk_score, timestamp=now)


@router.get("/hotspots", response_model=list[HotspotResponse])
def get_hotspots(
    grid_size: int = Query(7, ge=3, le=15),
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    center = REGION_CENTERS.get(settings.REGION, REGION_CENTERS["zimbabwe"])
    hotspots = generate_hotspots(
        center_lat=center["lat"],
        center_lng=center["lng"],
        grid_size=grid_size,
    )
    return hotspots


@router.get("/heatmap")
def get_heatmap(
    grid_size: int = Query(7, ge=3, le=15),
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    center = REGION_CENTERS.get(settings.REGION, REGION_CENTERS["zimbabwe"])
    hotspots = generate_hotspots(
        center_lat=center["lat"],
        center_lng=center["lng"],
        grid_size=grid_size,
    )
    return {
        "region": settings.REGION,
        "generated_at": datetime.utcnow().isoformat(),
        "cells": hotspots,
    }
