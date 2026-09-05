from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Equipment(Base):
    __tablename__ = "equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(30))
    serial_number = Column(String(100), unique=True)
    assigned_to = Column(Integer, ForeignKey("rangers.id"))
    status = Column(String(20), default="active")
    purchase_date = Column(DateTime)
    last_maintenance = Column(DateTime)
    next_maintenance = Column(DateTime)
    notes = Column(Text)
    current_location = Column(String(100))
    last_known_location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ranger = relationship("Ranger", backref="equipment")