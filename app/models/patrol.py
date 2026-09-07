from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Patrol(Base):
    __tablename__ = "patrols"
    
    id = Column(Integer, primary_key=True, index=True)
    route = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    ranger_id = Column(Integer, ForeignKey("rangers.id"), nullable=False)
    protected_area_id = Column(Integer, ForeignKey("protected_areas.id"))
    patrol_type = Column(String(30), default="routine")
    objectives = Column(Text)
    area_covered_km2 = Column(Float)
    status = Column(String(20), default="planned")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ranger = relationship("Ranger", backref="patrols")
    protected_area = relationship("ProtectedArea", backref="patrols")