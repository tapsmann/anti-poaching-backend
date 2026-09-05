from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Patrol(Base):
    __tablename__ = "patrols"
    
    id = Column(Integer, primary_key=True, index=True)
    route = Column(Geometry("LINESTRING", srid=4326), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    ranger_id = Column(Integer, ForeignKey("rangers.id"), nullable=False)
    protected_area_id = Column(Integer, ForeignKey("protected_areas.id"))
    patrol_type = Column(ENUM("routine", "intelligence_led", "rapid_response", "community_patrol", "aerial_surveillance", name="patrol_type"))
    objectives = Column(Text)
    area_covered_km2 = Column(Float)
    status = Column(ENUM("planned", "active", "completed", "cancelled", name="patrol_status"))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ranger = relationship("Ranger", backref="patrols")
    protected_area = relationship("ProtectedArea", backref="patrols")