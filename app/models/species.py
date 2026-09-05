from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Species(Base):
    __tablename__ = "species"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    scientific_name = Column(String(150))
    conservation_status = Column(ENUM("EX", "EW", "CR", "EN", "VU", "NT", "LC", "DD", "NE", name="conservation_status"))
    population_estimate = Column(Integer)
    habitat = Column(Text)
    threats = Column(Text)
    image_url = Column(String(500))
    geographic_range = Column(Geometry("POLYGON", srid=4326))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)