from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

incident_poacher = Table(
    "incident_poacher",
    Base.metadata,
    Column("incident_id", Integer, ForeignKey("incidents.id"), primary_key=True),
    Column("poacher_id", Integer, ForeignKey("poachers.id"), primary_key=True),
    Column("confirmed", Boolean, default=False),
    Column("notes", Text),
    Column("created_at", DateTime, default=datetime.utcnow)
)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(100), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    incident_type = Column(String(30), nullable=False)
    severity = Column(String(20))
    species_id = Column(Integer, ForeignKey("species.id"))
    protected_area_id = Column(Integer, ForeignKey("protected_areas.id"))
    ranger_id = Column(Integer, ForeignKey("rangers.id"))
    poacher_count = Column(Integer, default=0)
    evidence_photo = Column(String(500))
    verified = Column(Boolean, default=False)
    description = Column(Text)
    risk_score = Column(Float, default=0.0)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    species = relationship("Species", backref="incidents")
    protected_area = relationship("ProtectedArea", backref="incidents")
    ranger = relationship("Ranger", backref="incidents")