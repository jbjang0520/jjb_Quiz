from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuizRead,
    QuizWithQuestions
)
from app.services.quiz_service import get_quiz_with_questions, get_quizzes_for_user
from app.services.caching_service import get_cache
from app.crud.quiz import quiz_crud
from random import shuffle

router = APIRouter()

@router.post("/", response_model=QuizRead)
def create_quiz(
    quiz_in: QuizCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    새로운 퀴즈 생성
    관리자만 퀴즈를 생성할 수 있습니다.
    """
    quiz = quiz_crud.create_with_owner(db=db, obj_in=quiz_in, owner_id=current_user.id)
    return quiz

@router.get("/", response_model=List[QuizRead])
def read_quizzes(
    response: Response,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    퀴즈 목록 조회
    일반 사용자는 자신의 상태가 포함된 퀴즈 목록을, 관리자는 전체 목록을 조회할 수 있습니다.
    """
    cache = get_cache()
    cache_key = f"quizzes:list:user:{current_user.id}:skip:{skip}:limit:{limit}"
    cached_result = cache.get(cache_key)

    if cached_result:
        return cached_result

    if current_user.is_admin:
        quizzes = quiz_crud.get_multi_by_owner(db, owner_id=current_user.id, skip=skip, limit=limit)
    else:
        quizzes = get_quizzes_for_user(db, current_user, skip=skip, limit=limit)

    cache.set(cache_key, quizzes, expire=300)  # 5분 캐싱
    return quizzes

@router.get("/{quiz_id}", response_model=QuizWithQuestions)
def read_quiz(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
) -> Any:
    """
    퀴즈 상세 조회 (관리자는 고정된 순서, 사용자는 랜덤 출제 + 페이징)
    """
    quiz = get_quiz_with_questions(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")

    total_pool = quiz.questions[:]

    if not current_user.is_admin:
        # 사용자는 랜덤으로 문제 뽑기
        if quiz.randomize_questions:
            shuffle(total_pool)

        if quiz.questions_per_quiz:
            total_pool = total_pool[:quiz.questions_per_quiz]

        if quiz.randomize_options:
            for q in total_pool:
                shuffle(q.options)
    else:
        # 관리자는 문제 순서대로, questions_per_quiz 개수 제한만 적용
        if quiz.questions_per_quiz:
            total_pool = total_pool[:quiz.questions_per_quiz]
        # 선택지 순서도 고정 (shuffle 생략)

    # 페이징 적용
    total_questions = len(total_pool)
    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    paginated_questions = total_pool[start_idx:end_idx]

    result = {
        "id": quiz.id,
        "title": quiz.title,
        "description": quiz.description,
        "created_at": quiz.created_at,
        "updated_at": quiz.updated_at,
        "created_by": quiz.created_by,
        "is_active": quiz.is_active,
        "questions_per_quiz": quiz.questions_per_quiz,
        "randomize_questions": quiz.randomize_questions,
        "randomize_options": quiz.randomize_options,
        "questions": paginated_questions,
        "pagination": {
            "total": total_questions,
            "page": page,
            "items_per_page": items_per_page,
            "pages": (total_questions + items_per_page - 1) // items_per_page
        }
    }

    return result

@router.put("/{quiz_id}", response_model=QuizRead)
def update_quiz(
    quiz_id: int,
    quiz_in: QuizUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    퀴즈 수정
    관리자만 수정할 수 있습니다.
    """
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")

    quiz = quiz_crud.update(db=db, db_obj=quiz, obj_in=quiz_in)

    cache = get_cache()
    cache.clear_prefix(f"quiz:{quiz_id}")
    cache.clear_prefix("quizzes:list")

    return quiz

@router.delete("/{quiz_id}", response_model=QuizRead)
def delete_quiz(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    퀴즈 삭제
    관리자만 삭제할 수 있습니다.
    """
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="퀴즈를 찾을 수 없습니다.")

    quiz = quiz_crud.remove(db=db, id=quiz_id)

    cache = get_cache()
    cache.clear_prefix(f"quiz:{quiz_id}")
    cache.clear_prefix("quizzes:list")

    return quiz