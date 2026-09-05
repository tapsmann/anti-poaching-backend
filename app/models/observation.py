from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class PatrolObservation(Base):
    __tablename__ = "patrol_observations"
    
    id = Column(Integer, primary_key=True, index=True)
    patrol_id = Column(Integer, ForeignKey("patrols.id"), nullable=False)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    species_id = Column(Integer, ForeignKey("species.id"))
    ranger_id = Column(Integer, ForeignKey("rangers.id"))
    observation_type = Column(String(30), nullable=False)
    location = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    description = Column(Text)
    photo_url = Column(String(500))
    animal_count = Column(Integer)
    severity = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)