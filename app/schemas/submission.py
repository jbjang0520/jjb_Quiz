from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from .question import QuestionForUser

class AnswerSubmit(BaseModel):
    question_id: int = Field(..., example=1, description="문제 ID")
    selected_option_id: int = Field(..., example=3, description="사용자가 선택한 선택지 ID")

class SubmissionCreate(BaseModel):
    quiz_id: int = Field(..., example=42, description="응시할 퀴즈 ID")
    user_id: int = Field(..., example=202, description="응시한 사용자 ID")

class SubmissionUpdate(BaseModel):
    answers: Dict[str, int] = Field(
        ..., 
        example={"1": 3, "2": 5}, 
        description="문제 ID와 사용자가 선택한 선택지 ID 매핑"
    )

class SubmissionInDBBase(BaseModel):
    id: int = Field(..., example=1001, description="제출 ID")
    user_id: int = Field(..., example=202, description="응시한 사용자 ID")
    quiz_id: int = Field(..., example=42, description="해당 제출이 속한 퀴즈 ID")
    score: float = Field(..., example=80.0, description="채점된 점수")
    is_completed: bool = Field(..., example=True, description="퀴즈 완료 여부")
    created_at: datetime = Field(..., description="제출 생성 시간")
    updated_at: datetime = Field(..., description="제출 마지막 수정 시간")

    model_config = {
        "from_attributes": True
    }

class Submission(SubmissionInDBBase):
    answers: Dict[str, int] = Field(
        ..., 
        example={"1": 2, "2": 5}, 
        description="문제 ID와 선택지 ID 매핑 (사용자 응답)"
    )
    question_order: List[Dict[str, int]] = Field(
        ..., 
        example=[{"question_id": 1, "order_index": 0}, {"question_id": 2, "order_index": 1}],
        description="문제 순서 정보"
    )
    option_orders: Dict[str, List[Dict[str, int]]] = Field(
        ..., 
        example={"1": [{"option_id": 2, "order_index": 0}, {"option_id": 3, "order_index": 1}]},
        description="각 문제의 선택지 순서 정보"
    )

class SubmissionResult(BaseModel):
    id: int = Field(..., example=1001, description="제출 ID")
    quiz_id: int = Field(..., example=42, description="퀴즈 ID")
    score: float = Field(..., example=85.0, description="사용자의 점수")
    total_questions: int = Field(..., example=10, description="전체 문제 수")
    correct_answers: int = Field(..., example=8, description="맞힌 문제 수")
    created_at: datetime = Field(..., description="응시 시간")
    updated_at: datetime = Field(..., description="마지막 수정 시간")

class QuizSession(BaseModel):
    submission_id: int = Field(..., example=1001, description="진행 중인 제출 ID")
    questions: List[QuestionForUser] = Field(..., description="사용자에게 제공되는 문제 목록")
    current_answers: Dict[str, int] = Field(
        ..., 
        example={"1": 3}, 
        description="현재까지의 응답 상태 (문제 ID: 선택지 ID)"
    )

class SubmissionRead(SubmissionInDBBase):
    """
    기본 제출 정보 응답 스키마
    """
    pass

class SubmissionWithDetails(SubmissionInDBBase):
    questions: Optional[List[QuestionForUser]] = Field(
    default_factory=list,
    description="응시한 문제 목록"
    )
    answers: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description="응시자가 제출한 정답 (문제 ID: 선택지 ID)"
    )
    question_order: Optional[List[Dict[str, int]]] = Field(
        default_factory=list,
        description="문제 순서 정보"
    )
    option_orders: Optional[Dict[str, List[Dict[str, int]]]] = Field(
        default_factory=dict,
        description="각 문제의 선택지 순서 정보"
    )