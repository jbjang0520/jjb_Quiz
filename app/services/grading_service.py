from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.models.submission import Submission
from app.models.quiz import Quiz
from app.models.question import Question
from app.models.option import Option
from app.crud.question import question_crud
from app.crud.submission import submission_crud


def grade_submission(db: Session, submission: Submission, quiz: Quiz) -> Submission:
    """
    퀴즈 제출 결과를 채점하는 함수

    Args:
        db: 데이터베이스 세션
        submission: 채점 대상 제출 객체
        quiz: 해당 제출이 속한 퀴즈 객체 (문항 정보 포함)

    Returns:
        채점 결과가 반영된 Submission 객체
    """
    # dict 형태로 받은 답변 (question_id: selected_option_id)
    raw_answers = submission_crud.get_answers(db, submission.id)

    # 문자열 key가 있을 수 있으므로 int로 변환
    answered_questions = {
        int(question_id): selected_option_id
        for question_id, selected_option_id in raw_answers.items()
    }

    # 퀴즈의 모든 문항 가져오기
    questions = question_crud.get_questions_by_quiz(db, quiz_id=quiz.id)

    question_scores: Dict[int, bool] = {}
    total_points = 0
    max_points = 0

    for question in questions:
        max_points += 1
        correct_option_id = next((opt.id for opt in question.options if opt.is_correct), None)

        selected_option_id = answered_questions.get(question.id)

        if selected_option_id is not None and selected_option_id == correct_option_id:
            question_scores[question.id] = True
            total_points += 1
        else:
            question_scores[question.id] = False

    submission.score = (total_points / max_points * 100) if max_points > 0 else 0

    return submission


def get_submission_details(db: Session, submission: Submission) -> Dict[str, Any]:
    """
    제출 결과의 상세 정보를 반환하는 함수

    Args:
        db: 데이터베이스 세션
        submission: 대상 제출 객체

    Returns:
        질문, 사용자 선택, 정답 여부 등이 포함된 상세 정보 딕셔너리
    """
    # 제출된 답안 조회
    submission_answers = submission_crud.get_answers(db, submission.id)

    # 빠른 조회를 위해 question_id -> 선택된 option_id 형태로 변환
    answered_questions = {
        answer.question_id: answer.selected_option_id
        for answer in submission_answers
    }

    # 해당 퀴즈의 모든 문항 조회
    questions = question_crud.get_questions_by_quiz(db, quiz_id=submission.quiz_id)

    questions_details = []  # 상세 질문 정보 리스트

    for question in questions:
        options_data = []  # 옵션 목록
        correct_option_id = None

        # 각 옵션에 대한 정보 정리
        for option in question.options:
            if option.is_correct:
                correct_option_id = option.id  # 정답 옵션 확인

            options_data.append({
                "id": option.id,
                "text": option.text,  # 옵션 텍스트
                "is_correct": option.is_correct
            })

        # 응답 여부 및 정답 여부 확인
        is_answered = question.id in answered_questions
        is_correct = False
        selected_option_id = None

        if is_answered:
            selected_option_id = answered_questions[question.id]
            is_correct = selected_option_id == correct_option_id

        # 해당 문항의 상세 정보 구성
        question_detail = {
            "id": question.id,
            "text": question.text,
            "options": options_data,
            "selected_option_id": selected_option_id,
            "correct_option_id": correct_option_id,
            "is_answered": is_answered,
            "is_correct": is_correct
        }

        questions_details.append(question_detail)

    # 전체 제출 정보 반환
    return {
        "id": submission.id,
        "quiz_id": submission.quiz_id,
        "user_id": submission.user_id,
        "score": submission.score,
        "is_completed": submission.is_completed,
        "questions": questions_details,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at
    }