from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.ranger import Ranger

try:
    import bcrypt
    if not hasattr(bcrypt, '__about__'):
        pass
except ImportError:
    pass

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    expires = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": email, "purpose": "password_reset", "exp": expires},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def get_reset_email(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("purpose") != "password_reset" or not payload.get("sub"):
            raise ValueError("Invalid reset token")
        return str(payload["sub"])
    except (JWTError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token") from exc


def get_ranger_from_token(token: str, db: Session) -> Ranger:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        ranger_id: str = payload.get("sub")
        if ranger_id is None:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    ranger = db.query(Ranger).filter(Ranger.id == int(ranger_id)).first()
    if ranger is None or not ranger.is_active:
        raise credentials_exception
    return ranger


def get_current_ranger(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Ranger:
    return get_ranger_from_token(token, db)


def get_optional_ranger(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[Ranger]:
    if not token:
        return None
    try:
        return get_ranger_from_token(token, db)
    except HTTPException:
        return None


def require_admin(
    current_ranger: Ranger = Depends(get_current_ranger),
) -> Ranger:
    if current_ranger.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_ranger


def require_supervisor_or_admin(
    current_ranger: Ranger = Depends(get_current_ranger),
) -> Ranger:
    if current_ranger.role not in ("admin", "supervisor"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Supervisor or admin privileges required",
        )
    return current_ranger


def check_ranger_can_access_area(ranger: Ranger, area_id: Optional[int]) -> bool:
    if ranger.role in ("admin", "supervisor"):
        return True
    if area_id is None:
        return False
    if ranger.assigned_area_id is None:
        return False
    return ranger.assigned_area_id == area_id


def scope_to_ranger_area(query, ranger: Ranger, area_column):
    if ranger.role in ("admin", "supervisor"):
        return query
    if ranger.assigned_area_id is None:
        return query.filter(area_column == -1)
    return query.filter(area_column == ranger.assigned_area_id)


def check_ranger_can_modify(ranger: Ranger, target_ranger_id: Optional[int] = None) -> bool:
    if ranger.role == "admin":
        return True
    if ranger.role == "supervisor":
        return True
    if target_ranger_id and ranger.id == target_ranger_id:
        return True
    return False
