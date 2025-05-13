from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionInDBBase, 
    QuestionRead
)
from app.crud.question import question_crud
from app.crud.quiz import quiz_crud

router = APIRouter()


@router.post("/{quiz_id}/questions/", response_model=QuestionInDBBase)
def create_question(
    quiz_id: int,
    question_in: QuestionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    새로운 문제를 퀴즈에 추가합니다.
    관리자만 문제를 생성할 수 있습니다.
    """
    # 퀴즈가 존재하는지 확인
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="퀴즈를 찾을 수 없습니다"
        )
    
    return question_crud.create_with_quiz(db=db, obj_in=question_in, quiz_id=quiz_id)


@router.get("/{quiz_id}/questions/", response_model=List[QuestionRead])
def read_questions(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    특정 퀴즈에 대한 문제들을 가져옵니다.
    """
    # 퀴즈가 존재하는지 확인
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="퀴즈를 찾을 수 없습니다"
        )
    
    # 사용자가 관리자가 아닌 경우, 퀴즈가 랜덤 문제 순서가 활성화되어 있는지 확인
    if not current_user.is_admin:
        questions = question_crud.get_random_questions_for_quiz(
            db=db, 
            quiz_id=quiz_id, 
            user_id=current_user.id,
            skip=skip, 
            limit=limit
        )
    else:
        questions = question_crud.get_questions_by_quiz(
            db=db, 
            quiz_id=quiz_id, 
            skip=skip, 
            limit=limit
        )
    
    return questions


@router.get("/{quiz_id}/questions/{question_id}", response_model=QuestionRead)
def read_question(
    quiz_id: int,
    question_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    특정 문제를 ID로 조회합니다.
    """
    question = question_crud.get_question_for_quiz(db=db, quiz_id=quiz_id, question_id=question_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail="문제를 찾을 수 없습니다"
        )
    
    return question


@router.put("/{quiz_id}/questions/{question_id}", response_model=QuestionInDBBase)  # 수정: response_model을 QuestionInDBBase로 변경
def update_question(
    quiz_id: int,
    question_id: int,
    question_in: QuestionUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    문제를 업데이트합니다.
    관리자만 문제를 수정할 수 있습니다.
    """
    question = question_crud.get_question_for_quiz(db=db, quiz_id=quiz_id, question_id=question_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail="문제를 찾을 수 없습니다"
        )
    
    question = question_crud.update(db=db, db_obj=question, obj_in=question_in)
    return question


@router.delete("/{quiz_id}/questions/{question_id}", response_model=QuestionInDBBase)  # 수정: response_model을 QuestionInDBBase로 변경
def delete_question(
    quiz_id: int,
    question_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    문제를 삭제합니다.
    관리자만 문제를 삭제할 수 있습니다.
    """
    question = question_crud.get_question_for_quiz(db=db, quiz_id=quiz_id, question_id=question_id)
    if not question:
        raise HTTPException(
            status_code=404,
            detail="문제를 찾을 수 없습니다"
        )
    
    question = question_crud.remove(db=db, id=question_id)
    return question