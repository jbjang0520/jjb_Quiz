from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str  # 또는 사용 중인 payload 구조에 맞게 수정
    exp: Optional[int] = None