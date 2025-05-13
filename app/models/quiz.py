from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimeStampMixin

class Quiz(Base, TimeStampMixin):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    questions_per_quiz = Column(Integer, default=10)  # 출제할 문제 수
    randomize_questions = Column(Boolean, default=False)  # 문제 랜덤 배치 여부
    randomize_options = Column(Boolean, default=False)  # 선택지 랜덤 배치 여부
    
    # 관계 설정
    creator = relationship("User", foreign_keys=[created_by])
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="quiz", cascade="all, delete-orphan")