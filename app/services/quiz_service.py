from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import random

from app.models.quiz import Quiz
from app.models.question import Question
from app.models.option import Option
from app.models.submission import Submission
from app.models.user import User
from app.crud.quiz import quiz_crud
from app.crud.question import question_crud
from app.crud.submission import submission_crud
from app.schemas.quiz import QuizRead
from app.services.caching_service import get_cache
from app.crud.quiz import quiz_crud

def get_quiz_with_questions(db: Session, quiz_id: int) -> Quiz:
    """
    퀴즈와 해당 퀴즈의 모든 질문 및 옵션을 가져오는 함수.
    캐시에서 먼저 확인하고, 없으면 DB에서 가져옴.
    """
    # 캐시에서 먼저 확인
    cache = get_cache()
    cache_key = f"quiz:{quiz_id}:full"
    cached_quiz = cache.get(cache_key)

    if cached_quiz:
        return cached_quiz

    # 캐시에서 없으면 DB에서 퀴즈를 가져옴
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        return None

    # 관계된 질문들을 로드하도록 강제
    for question in quiz.questions:
        # 각 질문에 대해 옵션을 강제로 로드
        _ = question.options

    # 캐시에 결과를 저장 (5분 동안 유효)
    cache.set(cache_key, quiz, expire=300)  # 5분 동안 캐시

    return quiz

def get_questions_for_user(db: Session, quiz_id: int, user_id: int) -> List[Question]:
    """
    특정 사용자의 퀴즈 세션에 대한 질문을 가져오는 함수.
    퀴즈 설정에 따라 질문을 랜덤화하고, 사용자의 응시 상태에 맞게 반환.
    """
    # 퀴즈 정보를 가져옴
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        return []

    # 사용자의 기존 제출 정보가 있는지 확인하여 일관성 유지
    submission = submission_crud.get_in_progress_by_user_and_quiz(
        db=db, user_id=user_id, quiz_id=quiz_id
    )

    # 이미 제출한 질문이 있으면 그 질문을 사용
    if submission and hasattr(submission, 'selected_questions') and submission.selected_questions:
        question_ids = submission.selected_questions
        return question_crud.get_questions_by_ids(db=db, question_ids=question_ids)

    # 그렇지 않으면 퀴즈 설정에 맞게 질문을 선택
    all_questions = question_crud.get_all_by_quiz(db=db, quiz_id=quiz_id)

    # 퀴즈 설정에 따라 질문 수 제한이 있다면, 그 수에 맞게 질문을 랜덤 선택
    selected_questions = all_questions
    if quiz.questions_per_quiz and quiz.questions_per_quiz < len(all_questions):
        selected_questions = random.sample(all_questions, quiz.questions_per_quiz)

    # 퀴즈 설정에 따라 질문 랜덤화
    if quiz.randomize_questions:
        random.shuffle(selected_questions)

    # 각 질문에 대해 옵션을 랜덤화
    if quiz.randomize_options:
        for question in selected_questions:
            random.shuffle(question.options)

    # 새로운 세션이라면 선택된 질문을 저장
    if not submission:
        submission_data = {
            "quiz_id": quiz_id,
            "user_id": user_id,
            "is_completed": False,
            "score": 0,
            "selected_questions": [q.id for q in selected_questions]
        }
        submission_crud.create(db=db, obj_in=submission_data)

    return selected_questions

def get_user_quiz_status(db: Session, quiz_id: int, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
    """
    특정 사용자의 퀴즈 상태를 가져오는 함수.
    사용자의 응시 상태에 따라 'not_started', 'in_progress', 'completed' 상태를 반환.
    """
    # 퀴즈 정보를 가져옴
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        return {"status": "not_found"}

    # 제출 정보를 확인
    submissions = submission_crud.get_by_user_and_quiz(db=db, user_id=user_id, quiz_id=quiz_id, skip=skip, limit=limit)

    if not submissions:
        return {"status": "not_started", "quiz_title": quiz.title}

    # 진행 중인 제출이 있다면 해당 상태 반환
    in_progress = next((s for s in submissions if not s.is_completed), None)
    if in_progress:
        return {
            "status": "in_progress",
            "quiz_title": quiz.title,
            "submission_id": in_progress.id,
            "started_at": in_progress.created_at
        }

    # 아니면 가장 최근에 완료된 제출을 반환
    completed = sorted(submissions, key=lambda s: s.updated_at, reverse=True)[0]
    return {
        "status": "completed",
        "quiz_title": quiz.title,
        "submission_id": completed.id,
        "completed_at": completed.updated_at,
        "score": completed.score
    }

def get_quizzes_for_user(db: Session, user: User, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """
    사용자가 참여할 수 있는 퀴즈 목록을 가져오고, 각 퀴즈에 대해 사용자의 상태를 추가하여 반환.
    관리자가 아닌 경우 사용자 상태를 추가.
    """
    # 모든 활성화된 퀴즈를 가져옴
    quizzes = quiz_crud.get_multi(db=db, skip=skip, limit=limit)

    result = []
    for quiz in quizzes:
        # 사용자 상태를 확인
        status = get_user_quiz_status(db, quiz.id, user.id, skip, limit)

        # 사용자가 응시한 퀴즈만 추가
        if status["status"] != "not_started":
            quiz_data = {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "created_at": quiz.created_at,
                "total_questions": len(quiz.questions),
                "questions_per_quiz": quiz.questions_per_quiz or len(quiz.questions),
                "created_by": quiz.created_by,
                "is_active": quiz.is_active,
                "updated_at": quiz.updated_at,
                "status": status["status"]
            }

            if status["status"] != "not_started":
                quiz_data["submission_id"] = status.get("submission_id")
            if status["status"] == "completed":
                quiz_data["score"] = status.get("score")

            result.append(quiz_data)

    return result