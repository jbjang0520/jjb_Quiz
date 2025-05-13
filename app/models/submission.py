from sqlalchemy import Column, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimeStampMixin

class Submission(Base, TimeStampMixin):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    quiz_id = Column(Integer, ForeignKey("quizzes.id"))
    score = Column(Float, default=0.0)  # 점수
    is_completed = Column(Boolean, default=False)  # 제출 완료 여부
    question_order = Column(JSON)  # 사용자별 문제 순서 저장 [{question_id: 1, order: 2}, ...]
    option_orders = Column(JSON)  # 사용자별 선택지 순서 저장 {question_id: [{option_id: 1, order: 2}, ...], ...}
    answers = Column(JSON)  # 사용자 답변 저장 {question_id: option_id, ...}
    
    # 관계 설정
    user = relationship("User")
    quiz = relationship("Quiz", back_populates="submissions")