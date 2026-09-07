from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_ranger, require_admin
from app.models.ranger import Ranger
from app.models.species import Species
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "uploads", "species")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()

# --- Pydantic Schemas ---
class SpeciesCreate(BaseModel):
    name: str
    scientific_name: Optional[str] = None
    conservation_status: Optional[str] = None
    population_estimate: Optional[int] = None
    habitat: Optional[str] = None
    threats: Optional[str] = None
    image_url: Optional[str] = None

class SpeciesUpdate(BaseModel):
    name: Optional[str] = None
    scientific_name: Optional[str] = None
    conservation_status: Optional[str] = None
    population_estimate: Optional[int] = None
    habitat: Optional[str] = None
    threats: Optional[str] = None
    image_url: Optional[str] = None

class SpeciesResponse(BaseModel):
    id: int
    name: str
    scientific_name: Optional[str]
    conservation_status: Optional[str]
    population_estimate: Optional[int]
    habitat: Optional[str]
    threats: Optional[str]
    image_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# --- GET Routes ---
@router.get("/", response_model=List[SpeciesResponse])
def get_species(
    skip: int = 0,
    limit: int = 100,
    conservation_status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(Species)
    if conservation_status:
        query = query.filter(Species.conservation_status == conservation_status)
    species = query.offset(skip).limit(limit).all()
    return species

# --- SEARCH Route ---
@router.get("/search", response_model=List[SpeciesResponse])
def search_species(
    q: str = Query(..., min_length=1, description="Search term for species name or scientific name"),
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    species = db.query(Species).filter(
        or_(
            Species.name.ilike(f"%{q}%"),
            Species.scientific_name.ilike(f"%{q}%")
        )
    ).all()
    return species

# --- GET by ID Route ---
@router.get("/{species_id}", response_model=SpeciesResponse)
def get_species_by_id(
    species_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species

# --- POST Routes ---
@router.post("/", response_model=SpeciesResponse, status_code=201)
def create_species(
    species: SpeciesCreate,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    db_species = Species(**species.model_dump())
    db.add(db_species)
    db.commit()
    db.refresh(db_species)
    return db_species

# --- PUT Routes ---
@router.put("/{species_id}", response_model=SpeciesResponse)
def update_species(
    species_id: int,
    species: SpeciesUpdate,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    db_species = db.query(Species).filter(Species.id == species_id).first()
    if not db_species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    for key, value in species.model_dump(exclude_unset=True).items():
        setattr(db_species, key, value)
    
    db.commit()
    db.refresh(db_species)
    return db_species

# --- DELETE Routes ---
@router.delete("/{species_id}", status_code=204)
def delete_species(
    species_id: int,
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    db_species = db.query(Species).filter(Species.id == species_id).first()
    if not db_species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Delete associated image file if it exists
    if db_species.image_url and db_species.image_url.startswith("/uploads/species/"):
        file_path = os.path.join(os.path.dirname(UPLOAD_DIR), db_species.image_url.lstrip("/"))
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.delete(db_species)
    db.commit()

# --- UPLOAD Routes ---
@router.post("/upload", response_model=SpeciesResponse)
async def upload_species_image(
    species_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin: Ranger = Depends(require_admin),
):
    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")
    
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit")
    
    # Find species
    db_species = db.query(Species).filter(Species.id == species_id).first()
    if not db_species:
        raise HTTPException(status_code=404, detail="Species not found")
    
    # Delete old image if it exists
    if db_species.image_url and db_species.image_url.startswith("/uploads/species/"):
        old_path = os.path.join(os.path.dirname(UPLOAD_DIR), db_species.image_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)
    
    # Save new file
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Update species image_url
    image_url = f"/uploads/species/{filename}"
    db_species.image_url = image_url
    db.commit()
    db.refresh(db_species)
    return db_species
