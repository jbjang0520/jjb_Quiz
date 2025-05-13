from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.schemas.token import Token
from app.schemas.user import User,UserCreate
from app.crud.user import user

router = APIRouter()

@router.post("/token", response_model=Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    db_user = user.authenticate(db, email=form_data.username, password=form_data.password)
    if not db_user:
        print("❌ 인증 실패: 사용자 없음")
        raise AuthenticationError(detail="Incorrect email or password")
    if not db_user.is_active:
        print("❌ 인증 실패: 비활성 사용자")
        raise AuthenticationError(detail="Inactive user")

    print("✅ 인증 성공, 토큰 발급")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            db_user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=User)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    새 사용자를 등록합니다.
    """
    new_user = crud.user.get_by_email(db, email=user_in.email)
    if new_user:
        raise AuthenticationError(detail="Email already registered")
    
    return crud.user.create(db, obj_in=user_in)