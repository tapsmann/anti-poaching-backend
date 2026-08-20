from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class ProtectedArea(Base):
    __tablename__ = "protected_areas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    boundary = Column(Geometry("POLYGON", srid=4326), nullable=True)
    center_point = Column(Geometry("POINT", srid=4326), nullable=True)
    zone_type = Column(ENUM("national_park", "game_reserve", "wildlife_sanctuary", "conservation_area", "private_reserve", name="zone_type"))
    risk_level = Column(ENUM("low", "medium", "high", "critical", name="risk_level"))
    size_hectares = Column(Float)
    protected_since = Column(DateTime)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)