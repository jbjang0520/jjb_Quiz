from typing import Dict, List, Optional, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.models.submission import Submission
from app.models.question import Question
from app.models.option import Option
from app.models.quiz import Quiz
from app.models.session import Session as SessionModel
from app.schemas.submission import SubmissionCreate, SubmissionUpdate, AnswerSubmit
from app.crud.base import CRUDBase

class CRUDSubmission(CRUDBase[Submission, SubmissionCreate, SubmissionUpdate]):
    # 기존 메서드들...

    def get_answers(self, db: Session, submission_id: int) -> Dict[str, int]:
        """
        특정 제출에 대한 답변을 가져오는 메서드.
        """
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {}

        # 제출에 대한 답변을 가져오는 로직을 구현합니다.
        return submission.answers if hasattr(submission, 'answers') else {}

    def create_for_user(
        self,
        db: Session,
        *,
        user_id: int,
        quiz_id: int,
        question_order: List[Dict[str, int]],
        option_orders: Dict[str, List[Dict[str, int]]]
    ) -> Submission:
        """
        사용자의 퀴즈 세션을 생성합니다.
        """
        db_obj = Submission(
            user_id=user_id,
            quiz_id=quiz_id,
            is_completed=False,
            score=0.0,
            question_order=question_order,
            option_orders=option_orders,
            answers={}
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_answers(
        self, db: Session, *, submission_id: int, answers: Dict[str, int]
    ) -> Submission:
        """
        사용자의 답변을 업데이트합니다.
        """
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.answers = answers
            db.add(submission)
            db.commit()
            db.refresh(submission)
        return submission

    def get_by_user_and_quiz(self, db: Session, user_id: int, quiz_id: int, skip: int = 0, limit: int = 100):
        """
        사용자-퀴즈 조합으로 제출 정보를 찾습니다.
        """
        return db.query(self.model).filter(
            self.model.user_id == user_id,
            self.model.quiz_id == quiz_id
        ).offset(skip).limit(limit).all()

    def get_by_quiz_and_submission_id(self, db: Session, quiz_id: int, submission_id: int) -> Optional[Submission]:
        """
        퀴즈 ID와 제출 ID를 기준으로 제출 기록을 조회합니다.
        """
        return db.query(Submission).options(
            joinedload(Submission.quiz).joinedload(Quiz.questions)
        ).filter(
            Submission.id == submission_id,
            Submission.quiz_id == quiz_id
        ).first()

    def get_in_progress_by_user_and_quiz(self, db: Session, user_id: int, quiz_id: int):
        """
        완료되지 않은(submission.is_completed=False) 제출을 가져옵니다.
        """
        return (
            db.query(Submission)
            .filter(
                Submission.user_id == user_id,
                Submission.quiz_id == quiz_id,
                Submission.is_completed == False
            )
            .first()
        )

    def add_answers(self, db: Session, submission_id: int, answers_in: List[AnswerSubmit]) -> Submission:
        """
        여러 문제에 대한 답변을 저장하거나 갱신합니다.
        """
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return None

        # 기존 답변 딕셔너리에 갱신
        answers = submission.answers or {}

        # 여러 답안 처리
        for answer in answers_in:
            answers[str(answer.question_id)] = answer.selected_option_id

        submission.answers = answers

        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    def get_by_user(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Submission]:
        """
        사용자의 모든 제출 정보를 가져옵니다.
        """
        return (
            db.query(Submission)
            .filter(Submission.user_id == user_id)
            .order_by(desc(Submission.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def submit_quiz(
        self, db: Session, *, submission_id: int, answers: Dict[str, int]
    ) -> Submission:
        """
        퀴즈를 제출하고 자동 채점합니다.
        """
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return None

        # 답변 저장
        submission.answers = answers
        submission.is_completed = True

        # 채점
        total_questions = len(answers)
        correct_count = 0

        for question_id_str, option_id in answers.items():
            question_id = int(question_id_str)
            # 선택한 옵션이 정답인지 확인
            option = db.query(Option).filter(
                Option.id == option_id,
                Option.question_id == question_id,
                Option.is_correct == True
            ).first()

            if option:
                correct_count += 1

        # 점수 계산 (백분율)
        if total_questions > 0:
            submission.score = (correct_count / total_questions) * 100

        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    def save_session(
        self, db: Session, *, user_id: int, submission_id: int, current_answers: Dict[str, int]
    ) -> SessionModel:
        """
        현재 세션 상태를 저장합니다.
        """
        # 기존 세션이 있는지 확인
        session = (
            db.query(SessionModel)
            .filter(
                SessionModel.user_id == user_id,
                SessionModel.submission_id == submission_id
            )
            .first()
        )

        if session:
            # 기존 세션 업데이트
            session.current_answers = current_answers
        else:
            # 새 세션 생성
            session = SessionModel(
                user_id=user_id,
                submission_id=submission_id,
                session_id=f"session_{user_id}_{submission_id}",
                current_answers=current_answers
            )

        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_session(
        self, db: Session, *, user_id: int, submission_id: int
    ) -> Optional[SessionModel]:
        """
        저장된 세션을 가져옵니다.
        """
        return (
            db.query(SessionModel)
            .filter(
                SessionModel.user_id == user_id,
                SessionModel.submission_id == submission_id
            )
            .first()
        )

submission_crud = CRUDSubmission(Submission)