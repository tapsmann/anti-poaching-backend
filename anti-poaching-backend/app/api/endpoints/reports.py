from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.security import get_current_ranger
from app.models.report import CommunityReport
from app.models.ranger import Ranger
from app.schemas.schemas import ReportCreate, ReportResponse, ReportUpdate
from app.schemas.serializers import serialize_report
from app.services.ml_service import predict_risk_score

router = APIRouter()


@router.get("/", response_model=list[ReportResponse])
def get_reports(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    report_type: str | None = None,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    query = db.query(CommunityReport)
    if status:
        query = query.filter(CommunityReport.status == status)
    if report_type:
        query = query.filter(CommunityReport.report_type == report_type)
    reports = query.order_by(CommunityReport.created_at.desc()).offset(skip).limit(limit).all()
    return [serialize_report(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_by_id(
    report_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return serialize_report(report)


@router.post("/", response_model=ReportResponse, status_code=201)
def create_report(report: ReportCreate, db: Session = Depends(get_db)):
    """Public endpoint — anonymous community reports allowed."""
    risk = predict_risk_score(report.latitude, report.longitude)
    db_report = CommunityReport(
        location=point_from_latlng(report.latitude, report.longitude),
        description=report.description,
        reporter_phone=report.reporter_phone if not report.is_anonymous else None,
        reporter_email=report.reporter_email if not report.is_anonymous else None,
        is_anonymous=report.is_anonymous,
        report_type=report.report_type,
        risk_score=risk,
        status="pending",
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return serialize_report(db_report)


@router.put("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: int,
    report: ReportUpdate,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    for key, value in report.model_dump(exclude_unset=True).items():
        setattr(db_report, key, value)
    db.commit()
    db.refresh(db_report)
    return serialize_report(db_report)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: Ranger = Depends(get_current_ranger),
):
    db_report = db.query(CommunityReport).filter(CommunityReport.id == report_id).first()
    if not db_report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(db_report)
    db.commit()
