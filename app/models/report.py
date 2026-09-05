from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class CommunityReport(Base):
    __tablename__ = "community_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(Geometry("POINT", srid=4326), nullable=False)
    reporter_phone = Column(String(20))
    reporter_email = Column(String(100))
    is_anonymous = Column(Boolean, default=True)
    description = Column(Text, nullable=False)
    photo_url = Column(String(500))
    report_type = Column(ENUM("poaching", "suspicious_activity", "injured_animal", "fire", "illegal_activity", "information", name="report_type"))
    risk_score = Column(Float, default=0.0)
    status = Column(ENUM("pending", "verified", "investigating", "resolved", "dismissed", name="report_status"), default="pending")
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    assigned_ranger_id = Column(Integer, ForeignKey("rangers.id"))
    ranger_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assigned_ranger = relationship("Ranger", backref="assigned_reports")