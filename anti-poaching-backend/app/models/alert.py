from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import ENUM
from geoalchemy2 import Geometry
from app.core.database import Base
from datetime import datetime

class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"))
    alert_type = Column(ENUM("poaching_detected", "high_risk_zone", "ranger_emergency", "community_report", "patrol_alert", "system_alert", name="alert_type"), nullable=False)
    priority = Column(ENUM("low", "medium", "high", "critical", name="alert_priority"))
    message = Column(Text, nullable=False)
    location = Column(Geometry("POINT", srid=4326))
    radius_km = Column(Float)
    status = Column(ENUM("new", "sent", "acknowledged", "resolved", name="alert_status"), default="new")
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)