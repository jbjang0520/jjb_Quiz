from typing import Generator, Dict
from fastapi import Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.db.session import SessionLocal
from app.schemas.token import TokenPayload
from app.crud.user import user

# User 임포트 추가
from app.models.user import User

# OAuth2 인증 토큰을 가져오기 위한 설정
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# 데이터베이스 세션을 생성하고 반환하는 의존성 함수
def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# 현재 로그인한 유저를 토큰에서 추출해 반환
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="토큰에 사용자 정보가 없습니다."
            )
        token_data = TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="자격 증명을 확인할 수 없습니다."
        )

    # 사용자 정보 조회
    current_user = user.get(db, id=token_data.sub)
    if not current_user:
        raise HTTPException(status_code=404, detail="유저를 찾을 수 없습니다.")
    return current_user

# 현재 유저가 활성 상태인지 확인
def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 유저입니다.")
    return current_user

# 현재 유저가 관리자 권한이 있는지 확인
def get_current_admin_user(
    current_user: models.User = Depends(get_current_active_user),
) -> models.User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user

# 페이지네이션 파라미터(skip, limit)를 쿼리에서 받아오는 의존성 함수
def get_pagination_params(
    skip: int = Query(0, alias="offset", ge=0, description="건너뛸 항목 수"),
    limit: int = Query(10, le=100, description="가져올 항목 수 (최대 100)"),
) -> Dict[str, int]:
    """
    페이지네이션을 위한 쿼리 파라미터를 반환합니다.
    - offset: 건너뛸 항목 수 (기본값 0)
    - limit: 반환할 항목 수 (기본값 10, 최대 100)
    """
    return {"skip": skip, "limit": limit}