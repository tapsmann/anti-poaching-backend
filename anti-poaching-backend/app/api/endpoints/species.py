from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_current_ranger
from app.models.ranger import Ranger
from app.models.species import Species
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

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
    db: Session = Depends(get_db)
):
    """Get all species with optional filtering"""
    query = db.query(Species)
    if conservation_status:
        query = query.filter(Species.conservation_status == conservation_status)
    species = query.offset(skip).limit(limit).all()
    return species

# --- SEARCH Route (MUST come BEFORE /{species_id}) ---
@router.get("/search", response_model=List[SpeciesResponse])
def search_species(
    q: str = Query(..., min_length=1, description="Search term for species name or scientific name"),
    db: Session = Depends(get_db)
):
    """Search species by name or scientific_name"""
    species = db.query(Species).filter(
        or_(
            Species.name.ilike(f"%{q}%"),
            Species.scientific_name.ilike(f"%{q}%")
        )
    ).all()
    return species

# --- GET by ID Route (MUST come AFTER /search) ---
@router.get("/{species_id}", response_model=SpeciesResponse)
def get_species_by_id(species_id: int, db: Session = Depends(get_db)):
    """Get a single species by ID"""
    species = db.query(Species).filter(Species.id == species_id).first()
    if not species:
        raise HTTPException(status_code=404, detail="Species not found")
    return species

# --- POST Routes ---
@router.post("/", response_model=SpeciesResponse, status_code=201)
def create_species(
    species: SpeciesCreate,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    """Create a new species"""
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
    db: Session = Depends(get_db)
):
    """Update an existing species"""
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
def delete_species(species_id: int, db: Session = Depends(get_db)):
    """Delete a species"""
    db_species = db.query(Species).filter(Species.id == species_id).first()
    if not db_species:
        raise HTTPException(status_code=404, detail="Species not found")
    db.delete(db_species)
    db.commit()
    return {"message": "Species deleted successfully"}