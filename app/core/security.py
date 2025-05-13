from datetime import datetime, timedelta
from typing import Any, Union, Optional

from jose import jwt  # JWT 토큰 생성을 위한 라이브러리
from passlib.context import CryptContext  # 비밀번호 해시화를 위한 라이브러리
from fastapi.security import OAuth2PasswordBearer  # OAuth2 인증을 위한 FastAPI 클래스

from app.core.config import settings  # 설정 정보 불러오기

# 비밀번호 암호화 설정 (bcrypt 알고리즘 사용)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2를 위한 토큰 URL 설정 (/api/v1/auth/login 엔드포인트 사용)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    액세스 토큰(JWT)을 생성하는 함수

    Args:
        subject: 토큰에 담을 사용자 식별자 (예: user_id 또는 email)
        expires_delta: 토큰 만료 기간 (지정하지 않으면 기본값 사용)

    Returns:
        JWT 문자열
    """
    # 만료 시간 설정
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # 토큰에 담을 데이터 (만료 시간, 사용자 정보)
    to_encode = {"exp": expire, "sub": str(subject)}

    # JWT 토큰 생성 (HS256 알고리즘 사용)
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    입력된 비밀번호와 해시된 비밀번호가 일치하는지 검증하는 함수

    Args:
        plain_password: 사용자가 입력한 비밀번호
        hashed_password: DB에 저장된 해시된 비밀번호

    Returns:
        일치 여부 (True/False)
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    비밀번호를 해시화하는 함수

    Args:
        password: 원본 비밀번호

    Returns:
        해시된 비밀번호 문자열
    """
    return pwd_context.hash(password)