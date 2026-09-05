from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Ranger(Base):
    __tablename__ = "rangers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    badge_number = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20))
    role = Column(String(20), default="ranger", nullable=False)
    rank = Column(String(20))
    specialization = Column(String(30))
    base_location = Column(String(100))
    current_location = Column(String(100))
    last_known_location = Column(String(100))
    assigned_area_id = Column(Integer, ForeignKey("protected_areas.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_on_duty = Column(Boolean, default=False)
    password_hash = Column(String(255))
    hire_date = Column(DateTime)
    emergency_contact = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_area = relationship("ProtectedArea", backref="assigned_rangers")