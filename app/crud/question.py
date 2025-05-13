from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import random

from app.models.question import Question
from app.models.option import Option
from app.schemas.question import QuestionCreate, QuestionUpdate, OptionCreate
from app.crud.base import CRUDBase

class CRUDQuestion(CRUDBase[Question, QuestionCreate, QuestionUpdate]):
    def create_with_quiz(
        self, db: Session, *, obj_in: QuestionCreate, quiz_id: int
    ) -> Question:
        """
        새로운 문제를 퀴즈에 추가합니다.
        """
        # 정답이 하나인지 검증
        correct_count = sum(1 for option in obj_in.options if option.is_correct)
        if correct_count != 1:
            raise HTTPException(status_code=400, detail="정답은 반드시 하나여야 합니다.")

        # 문제 생성
        db_question = Question(
            content=obj_in.content,
            quiz_id=quiz_id
        )
        db.add(db_question)
        db.flush()  # ID 할당을 위해 flush

        # 선택지 생성
        for i, option_data in enumerate(obj_in.options):
            db_option = Option(
                content=option_data.content,
                is_correct=option_data.is_correct,
                question_id=db_question.id,
                order_index=i
            )
            db.add(db_option)

        db.commit()
        db.refresh(db_question)
        return db_question

    def create_with_options(self, db: Session, *, obj_in: QuestionCreate) -> Question:
        # 이제 quiz_crud를 사용할 수 있습니다.
        # 정답이 하나인지 검증
        correct_count = sum(1 for option in obj_in.options if option.is_correct)
        if correct_count != 1:
            raise HTTPException(status_code=400, detail="정답은 반드시 하나여야 합니다.")

        # 문제 생성
        db_question = Question(
            content=obj_in.content,
            quiz_id=obj_in.quiz_id
        )
        db.add(db_question)
        db.flush()  # ID 할당을 위해 flush

        # 선택지 생성
        for i, option_data in enumerate(obj_in.options):
            db_option = Option(
                content=option_data.content,
                is_correct=option_data.is_correct,
                question_id=db_question.id,
                order_index=i
            )
            db.add(db_option)

        db.commit()
        db.refresh(db_question)
        return db_question

    def update_with_options(
        self, db: Session, *, db_obj: Question, obj_in: QuestionUpdate
    ) -> Question:
        # 문제 내용 업데이트
        if obj_in.content is not None:
            db_obj.content = obj_in.content

        # 선택지 업데이트
        if obj_in.options:
            # 기존 선택지 삭제
            db.query(Option).filter(Option.question_id == db_obj.id).delete()

            # 새 선택지 추가
            for i, option_data in enumerate(obj_in.options):
                db_option = Option(
                    content=option_data.content,
                    is_correct=option_data.is_correct,
                    question_id=db_obj.id,
                    order_index=i
                )
                db.add(db_option)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_questions_by_quiz(
        self, db: Session, *, quiz_id: int, skip: int = 0, limit: int = 100
    ) -> List[Question]:
        """
        특정 퀴즈의 모든 문제를 가져옵니다.
        """
        return (
            db.query(Question)
            .filter(Question.quiz_id == quiz_id)
            .order_by(Question.order_index)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_random_questions_for_quiz(self, db: Session, quiz_id: int, user_id: int, skip: int = 0, limit: int = 100) -> List[Question]:
        """
        특정 퀴즈에 대한 랜덤 문제를 가져오는 메서드.
        """
        questions = db.query(Question).filter(Question.quiz_id == quiz_id).offset(skip).limit(limit).all()
        if len(questions) <= limit:
            return questions
        return random.sample(questions, limit)

    def randomize_options(self, options: List[Option]) -> List[Dict]:
        """
        선택지 순서를 섞어서 반환합니다.
        """
        option_list = [
            {"id": opt.id, "content": opt.content, "order_index": i}
            for i, opt in enumerate(random.sample(options, len(options)))
        ]
        return option_list

    def get_questions_for_user(
        self,
        db: Session,
        *,
        quiz_id: int,
        randomize_questions: bool = False,
        randomize_options: bool = False,
        question_count: Optional[int] = None,
        existing_order: Optional[List[Dict[str, int]]] = None,
        existing_option_orders: Optional[Dict[str, List[Dict[str, int]]]] = None
    ) -> tuple:
        """
        사용자에게 제공할 문제와 선택지를 준비합니다.
        기존 순서가 있으면 그대로 사용하고, 없으면 새로 생성합니다.
        """
        # 모든 문제 가져오기
        all_questions = self.get_questions_by_quiz(db, quiz_id=quiz_id)

        # 출제할 문제 수 결정
        if question_count and question_count < len(all_questions):
            if existing_order:
                # 기존 순서에서 문제 ID 추출
                question_ids = [item["question_id"] for item in existing_order]
                questions = [q for q in all_questions if q.id in question_ids]
            else:
                # 무작위로 문제 선택
                questions = random.sample(all_questions, question_count)
        else:
            questions = all_questions

        # 문제 순서 결정
        question_order = []
        if existing_order:
            question_order = existing_order
        else:
            if randomize_questions:
                # 무작위 순서
                for i, q in enumerate(random.sample(questions, len(questions))):
                    question_order.append({"question_id": q.id, "order": i})
            else:
                # 기본 순서
                for i, q in enumerate(questions):
                    question_order.append({"question_id": q.id, "order": i})

        # 선택지 순서 결정
        option_orders = {}
        if existing_option_orders:
            option_orders = existing_option_orders
        else:
            for q in questions:
                options = db.query(Option).filter(Option.question_id == q.id).all()
                if randomize_options:
                    # 무작위 순서
                    option_orders[str(q.id)] = self.randomize_options(options)
                else:
                    # 기본 순서
                    option_orders[str(q.id)] = [
                        {"option_id": opt.id, "order": opt.order_index}
                        for opt in options
                    ]

        return questions, question_order, option_orders

question_crud = CRUDQuestion(Question)