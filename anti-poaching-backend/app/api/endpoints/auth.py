from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.geo import point_from_latlng
from app.core.config import settings
from app.core.security import create_access_token, create_password_reset_token, get_current_ranger, get_password_hash, get_reset_email, verify_password
from app.models.ranger import Ranger
from app.schemas.schemas import PasswordChangeRequest, PasswordResetConfirm, PasswordResetRequest, RangerCreate, RangerResponse, TokenResponse
from app.schemas.serializers import serialize_ranger

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    ranger = db.query(Ranger).filter(Ranger.email == form_data.username).first()
    if not ranger or not verify_password(form_data.password, ranger.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": str(ranger.id)})
    return TokenResponse(access_token=token, ranger=serialize_ranger(ranger))


@router.get("/me", response_model=RangerResponse)
def get_me(ranger: Ranger = Depends(get_current_ranger)):
    return serialize_ranger(ranger)


@router.post("/register", response_model=RangerResponse, status_code=201)
def register_ranger(ranger_in: RangerCreate, db: Session = Depends(get_db)):
    existing = db.query(Ranger).filter(
        (Ranger.email == ranger_in.email) | (Ranger.badge_number == ranger_in.badge_number)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ranger with this email or badge already exists")

    data = ranger_in.model_dump(exclude={"password", "latitude", "longitude"})
    db_ranger = Ranger(**data, password_hash=get_password_hash(ranger_in.password))
    if ranger_in.latitude is not None and ranger_in.longitude is not None:
        loc = point_from_latlng(ranger_in.latitude, ranger_in.longitude)
        db_ranger.base_location = loc
        db_ranger.current_location = loc

    db.add(db_ranger)
    db.commit()
    db.refresh(db_ranger)
    return serialize_ranger(db_ranger)


@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a reset token; connect this to email/SMS before production."""
    ranger = db.query(Ranger).filter(Ranger.email == payload.email).first()
    response = {"message": "If the account exists, password reset instructions have been sent."}
    if ranger and settings.ENVIRONMENT.lower() != "production":
        response["reset_token"] = create_password_reset_token(ranger.email)
    return response


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    email = get_reset_email(payload.token)
    ranger = db.query(Ranger).filter(Ranger.email == email).first()
    if not ranger:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    ranger.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password reset successfully. You can now sign in."}


@router.post("/change-password")
def change_password(payload: PasswordChangeRequest, ranger: Ranger = Depends(get_current_ranger), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, ranger.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    ranger.password_hash = get_password_hash(payload.new_password)
    db.commit()
    return {"message": "Password changed successfully."}
