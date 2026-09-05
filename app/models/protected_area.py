from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class ProtectedArea(Base):
    __tablename__ = "protected_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    boundary = Column(String(500), nullable=True)
    center_point = Column(String(100), nullable=True)
    zone_type = Column(String(20), default="national_park")
    risk_level = Column(String(20), default="medium")
    size_hectares = Column(Float)
    protected_since = Column(DateTime)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)