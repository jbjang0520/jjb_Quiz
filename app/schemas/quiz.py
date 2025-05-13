from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .question import QuestionRead

class QuizBase(BaseModel):
    title: str = Field(..., example="Python 기초 퀴즈", description="퀴즈 제목")
    description: Optional[str] = Field(None, example="파이썬 기초 문법에 대한 퀴즈입니다.", description="퀴즈 설명 (선택)")
    questions_per_quiz: int = Field(10, ge=1, example=5, description="응시 시 출제될 문제 수")
    randomize_questions: bool = Field(False, example=True, description="문제 출제 순서를 무작위로 설정할지 여부")
    randomize_options: bool = Field(False, example=True, description="선택지 순서를 무작위로 설정할지 여부")

class QuizCreate(QuizBase):
    """
    퀴즈 생성 시 사용하는 스키마
    """
    pass

class QuizUpdate(QuizBase):
    """
    퀴즈 수정 시 사용하는 스키마
    """
    title: Optional[str] = Field(None, example="수정된 퀴즈 제목", description="(선택) 퀴즈 제목")
    is_active: Optional[bool] = Field(None, example=True, description="(선택) 퀴즈 활성화 여부")

class QuizInDBBase(QuizBase):
    """
    DB에서 조회된 퀴즈 공통 필드
    """
    id: int = Field(..., example=1, description="퀴즈 고유 ID")
    created_by: int = Field(..., example=3, description="퀴즈 생성자 ID")
    is_active: bool = Field(..., example=True, description="퀴즈 활성화 상태")
    created_at: datetime = Field(..., description="퀴즈 생성 일시")
    updated_at: datetime = Field(..., description="퀴즈 마지막 수정 일시")

    class Config:
        orm_mode = True

class Quiz(QuizInDBBase):
    """
    일반 퀴즈 정보 출력용
    """
    pass

class QuizWithStatus(Quiz):
    """
    사용자의 퀴즈 응시 상태 정보를 포함한 응답
    """
    has_attempted: bool = Field(False, example=True, description="사용자가 해당 퀴즈에 응시한 적이 있는지 여부")
    has_completed: bool = Field(False, example=False, description="사용자가 해당 퀴즈를 완료했는지 여부")
    submission_id: Optional[int] = Field(None, example=101, description="마지막 제출 ID (있다면)")

class QuizRead(QuizInDBBase):
    """
    퀴즈 조회 응답용 스키마
    """
    pass

class QuizWithQuestions(QuizRead):
    """
    퀴즈 + 문제 리스트 반환용 스키마
    """
    questions: List[QuestionRead] = Field(..., description="해당 퀴즈에 포함된 문제 목록")