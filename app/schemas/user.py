from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr = Field(..., example="user@example.com", description="사용자의 이메일 주소")

    model_config = {
        "from_attributes": True
    }

class UserCreate(UserBase):
    password: str = Field(..., example="securepassword123", description="사용자의 비밀번호")

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, example="newpassword456", description="변경할 비밀번호 (선택)")
    is_active: Optional[bool] = Field(None, example=True, description="계정 활성화 여부")
    is_admin: Optional[bool] = Field(None, example=False, description="관리자 권한 여부")

class UserInDBBase(UserBase):
    id: int = Field(..., example=1, description="사용자 ID")
    is_active: bool = Field(..., example=True, description="활성화 상태")
    is_admin: bool = Field(..., example=False, description="관리자 권한 여부")

    model_config = {
        "from_attributes": True
    }

class User(UserInDBBase):
    """응답용 사용자 정보"""
    pass

class UserInDB(UserInDBBase):
    hashed_password: str = Field(..., example="$2b$12$...", description="해시된 비밀번호")