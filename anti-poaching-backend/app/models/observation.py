from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class PatrolObservation(Base):
    __tablename__ = "patrol_observations"
    
    id = Column(Integer, primary_key=True, index=True)
    patrol_id = Column(Integer, ForeignKey("patrols.id"), nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    species_id = Column(Integer, ForeignKey("species.id"))
    ranger_id = Column(Integer, ForeignKey("rangers.id"))
    observation_type = Column(ENUM("poaching_sign", "animal_sighting", "suspicious_activity", "snare_found", "track_found", "carcass_found", "illegal_camp", "fire_detected", name="observation_type"), nullable=False)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    photo_url = Column(String(500))
    animal_count = Column(Integer)
    severity = Column(ENUM("low", "medium", "high", "critical", name="severity"))
    created_at = Column(DateTime, default=datetime.utcnow)