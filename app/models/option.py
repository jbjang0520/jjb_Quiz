from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base, TimeStampMixin

class Option(Base, TimeStampMixin):
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    content = Column(Text)
    is_correct = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)  # 기본 선택지 순서
    
    # 관계 설정
    question = relationship("Question", back_populates="options")