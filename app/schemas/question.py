from typing import List, Optional, Annotated
from pydantic import BaseModel, Field
from pydantic.types import conlist
from datetime import datetime

# 옵션(선택지) 관련 모델
class OptionBase(BaseModel):
    content: str = Field(..., example="정답입니다", description="선택지 내용")
    is_correct: bool = Field(False, example=True, description="정답 여부")

class OptionCreate(OptionBase):
    """
    선택지 생성용 스키마
    """
    pass

class OptionUpdate(BaseModel):
    content: Optional[str] = Field(None, example="변경된 선택지", description="선택지 내용 (선택)")
    is_correct: Optional[bool] = Field(None, example=False, description="정답 여부 (선택)")

class OptionInDBBase(OptionBase):
    id: int = Field(..., example=1, description="선택지 고유 ID")
    question_id: int = Field(..., example=10, description="해당 선택지가 속한 문제의 ID")
    order_index: int = Field(..., example=0, description="선택지 순서")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = {
        "from_attributes": True
    }

class Option(OptionInDBBase):
    """
    전체 옵션 정보를 포함한 응답용
    """
    pass

class OptionForUser(BaseModel):
    id: int = Field(..., example=3, description="선택지 ID")
    content: str = Field(..., example="선택지 내용", description="사용자에게 보여질 선택지 내용")
    order_index: int = Field(..., example=1, description="선택지 순서")

    model_config = {
        "from_attributes": True
    }

# 문제 관련 모델
class QuestionBase(BaseModel):
    content: str = Field(..., example="파이썬에서 리스트를 선언하는 방법은?", description="문제 내용")
    quiz_id: int = Field(..., example=5, description="해당 문제가 속한 퀴즈 ID")

class QuestionCreate(QuestionBase):
    options: Annotated[List[OptionCreate], Field(min_items=3)] = Field(
    ..., description="해당 문제에 대한 선택지 목록 (최소 3개)"
)

class QuestionUpdate(BaseModel):
    content: Optional[str] = Field(None, example="수정된 문제 내용", description="문제 내용 (선택)")
    options: Optional[List[OptionUpdate]] = Field(None, description="선택지 목록 (선택)")

class QuestionInDBBase(QuestionBase):
    id: int = Field(..., example=100, description="문제 고유 ID")
    order_index: int = Field(..., example=2, description="문제 순서")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    model_config = {
        "from_attributes": True
    }

class Question(QuestionInDBBase):
    options: List[Option] = Field(..., description="문제에 대한 전체 선택지 정보")

class QuestionForUser(BaseModel):
    id: int = Field(..., example=12, description="문제 ID")
    content: str = Field(..., example="다음 중 파이썬의 키워드는?", description="문제 내용")
    order_index: int = Field(..., example=1, description="문제 순서")
    options: List[OptionForUser] = Field(..., description="사용자에게 보여질 선택지 목록")

    model_config = {
        "from_attributes": True
    }

class QuestionRead(BaseModel):
    id: int = Field(..., example=15, description="문제 ID")
    content: str = Field(..., example="파이썬에서 튜플을 선언하는 방법은?", description="문제 내용")
    order_index: int = Field(..., example=0, description="문제 순서")
    options: List[OptionForUser] = Field(..., description="선택지 목록")

    model_config = {
        "from_attributes": True
    }