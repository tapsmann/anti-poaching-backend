from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Poacher(Base):
    __tablename__ = "poachers"
    
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String(100))
    description = Column(Text)
    known_affiliate = Column(String(200))
    last_known_location = Column(Geometry("POINT", srid=4326))
    last_seen = Column(DateTime)
    threat_level = Column(ENUM("low", "medium", "high", "critical", name="threat_level"))
    methods_used = Column(Text)
    target_species = Column(String(200))
    estimated_age = Column(Integer)
    nationality = Column(String(100))
    identifying_marks = Column(Text)
    is_captured = Column(Boolean, default=False)
    captured_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)