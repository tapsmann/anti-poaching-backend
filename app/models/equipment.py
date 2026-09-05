from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(ENUM("vehicle", "drone", "camera", "radio", "tracking_device", "firearm", "survival_gear", "medical_kit", "k9_unit", name="equipment_type"))
    serial_number = Column(String(100), unique=True)
    assigned_to = Column(Integer, ForeignKey("rangers.id"))
    status = Column(ENUM("active", "maintenance", "damaged", "lost", "retired", name="equipment_status"))
    purchase_date = Column(DateTime)
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)
    notes = Column(Text)
    current_location = Column(Geometry("POINT", srid=4326))
    last_known_location = Column(Geometry("POINT", srid=4326))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)