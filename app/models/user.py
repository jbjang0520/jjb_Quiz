from sqlalchemy import Boolean, Column, Integer, String
from app.models.base import Base, TimeStampMixin

class User(Base, TimeStampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True, index=True)  # 자주 조회되는 컬럼에 인덱스 추가
    is_admin = Column(Boolean, default=False, index=True)  # 자주 조회되는 컬럼에 인덱스 추가