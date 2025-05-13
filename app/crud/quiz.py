from fastapi.encoders import jsonable_encoder
import random
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.quiz import Quiz
from app.models.question import Question
from app.models.option import Option
from app.models.submission import Submission
from app.schemas.quiz import QuizCreate, QuizUpdate
from app.crud.base import CRUDBase

class CRUDQuiz(CRUDBase[Quiz, QuizCreate, QuizUpdate]):
    def get(self, db: Session, id: int) -> Optional[Quiz]:
        """
        주어진 ID로 퀴즈를 조회합니다.
        """
        return db.query(Quiz).filter(Quiz.id == id).first()

    def create_with_owner(
        self, db: Session, *, obj_in: QuizCreate, owner_id: int
    ) -> Quiz:
        """
        새로운 퀴즈를 생성하고 생성자를 지정합니다.
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, created_by=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
            self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
        ) -> List[Quiz]:
            """
            주어진 관리자 ID로 퀴즈 목록을 조회합니다.
            """
            return (
                db.query(self.model)
                .filter(Quiz.created_by == owner_id)  # 필터링 기준은 created_by
                .offset(skip)
                .limit(limit)
                .all()
            )

    def get_random_questions(
        self, db: Session, *, quiz_id: int, count: int
    ) -> List[Question]:
        """
        퀴즈에서 무작위로 문제를 선택합니다.
        """
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).all()
        if len(questions) <= count:
            return questions
        return random.sample(questions, count)

    def get_active_quizzes(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Quiz]:
        """
        활성화된 퀴즈 목록만 가져옵니다.
        """
        return (
            db.query(self.model)
            .filter(Quiz.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_quizzes_with_status(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        """
        사용자의 퀴즈 응시 상태를 포함한 퀴즈 목록을 가져옵니다.
        """
        quizzes = (
            db.query(Quiz)
            .filter(Quiz.is_active == True)
            .offset(skip)
            .limit(limit)
            .all()
        )

        result = []
        for quiz in quizzes:
            # 해당 퀴즈에 대한 사용자의 제출 정보를 찾습니다
            submission = (
                db.query(Submission)
                .filter(
                    Submission.quiz_id == quiz.id,
                    Submission.user_id == user_id
                )
                .order_by(Submission.created_at.desc())
                .first()
            )

            quiz_dict = {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "questions_per_quiz": quiz.questions_per_quiz,
                "randomize_questions": quiz.randomize_questions,
                "randomize_options": quiz.randomize_options,
                "created_by": quiz.created_by,
                "is_active": quiz.is_active,
                "created_at": quiz.created_at,
                "updated_at": quiz.updated_at,
                "has_attempted": bool(submission),
                "has_completed": bool(submission and submission.is_completed),
                "submission_id": submission.id if submission else None
            }
            result.append(quiz_dict)

        return result

quiz_crud = CRUDQuiz(Quiz)