from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.endpoints import (
    alerts,
    auth,
    equipment,
    incidents,
    observations,
    patrols,
    poachers,
    predictions,
    protected_areas,
    rangers,
    reports,
    species,
    stats,
)
from app.core.config import settings
from app.core.database import engine, init_db

import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Anti-Poaching System API",
    description="Wildlife conservation and anti-poaching management system",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://(?:[a-z0-9-]+\.)?vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(species.router, prefix="/api/species", tags=["Species"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(patrols.router, prefix="/api/patrols", tags=["Patrols"])
app.include_router(rangers.router, prefix="/api/rangers", tags=["Rangers"])
app.include_router(protected_areas.router, prefix="/api/protected-areas", tags=["Protected Areas"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(equipment.router, prefix="/api/equipment", tags=["Equipment"])
app.include_router(observations.router, prefix="/api/observations", tags=["Observations"])
app.include_router(poachers.router, prefix="/api/poachers", tags=["Poachers"])

# Mount uploads directory for serving static files
uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    return {
        "message": "Anti-Poaching System API",
        "docs": "/docs",
        "version": "2.0.0",
        "region": settings.REGION,
    }


@app.get("/health")
async def health_check():
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False
    return {"status": "healthy" if db_ok else "degraded", "database": "connected" if db_ok else "disconnected"}