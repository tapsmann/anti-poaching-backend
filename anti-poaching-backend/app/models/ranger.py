from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Ranger(Base):
    __tablename__ = "rangers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    badge_number = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    rank = Column(ENUM("trainee", "officer", "senior_officer", "inspector", "commander", name="rank"))
    specialization = Column(ENUM("patrol", "investigation", "intelligence", "community_outreach", "quick_response", "k9_unit", "marine_unit", name="specialization"))
    base_location = Column(Geometry("POINT", srid=4326))
    current_location = Column(Geometry("POINT", srid=4326))
    last_known_location = Column(Geometry("POINT", srid=4326))
    is_active = Column(Boolean, default=True)
    is_on_duty = Column(Boolean, default=False)
    password_hash = Column(String(255))
    hire_date = Column(DateTime)
    emergency_contact = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)