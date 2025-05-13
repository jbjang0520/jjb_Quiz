from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from app.models.base import Base, TimeStampMixin

class Session(Base, TimeStampMixin):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    session_id = Column(String, index=True)  # 세션 ID
    current_answers = Column(JSON)  # 현재 답변 상태 {question_id: option_id, ...}