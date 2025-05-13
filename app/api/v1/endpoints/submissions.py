from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.models.quiz import Quiz
from app.schemas.submission import (
    SubmissionCreate, 
    SubmissionRead, 
    SubmissionUpdate,
    SubmissionWithDetails,
    AnswerSubmit
)
from app.schemas.question import QuestionForUser
from app.crud.submission import submission_crud
from app.crud.quiz import quiz_crud
from app.services.grading_service import grade_submission
from app.services.quiz_service import get_quiz_with_questions

router = APIRouter()


@router.post("/{quiz_id}/submissions/", response_model=SubmissionRead)
def create_submission(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    새로운 퀴즈 응시 기록(submission)을 생성합니다.
    (응답에는 아직 답안은 포함되지 않습니다)
    """
    # 퀴즈가 존재하는지 확인
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="퀴즈를 찾을 수 없습니다."
        )
    
    # 이미 해당 퀴즈에 응시 중인 기록이 있는지 확인
    existing_submission = submission_crud.get_in_progress_by_user_and_quiz(
        db=db, user_id=current_user.id, quiz_id=quiz_id
    )
    
    if existing_submission:
        # 기존 응시 기록이 있다면 그걸 반환
        return existing_submission
    
    # 새 응시 기록 생성
    submission_in = SubmissionCreate(
        quiz_id=quiz_id,
        user_id=current_user.id,
        is_completed=False,
        score=0
    )
    
    return submission_crud.create(db=db, obj_in=submission_in)


@router.get("/{quiz_id}/submissions/", response_model=List[SubmissionRead])
def read_submissions(
    quiz_id: int,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    특정 퀴즈에 대한 모든 응시 기록을 조회합니다.
    일반 사용자는 본인의 응시 기록만 조회 가능하고, 관리자는 전체 조회가 가능합니다.
    """
    quiz = quiz_crud.get(db=db, id=quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=404,
            detail="퀴즈를 찾을 수 없습니다."
        )
    
    if current_user.is_admin:
        submissions = submission_crud.get_by_quiz(
            db=db, quiz_id=quiz_id, skip=skip, limit=limit
        )
    else:
        # `user_id`는 `current_user.id`에서 가져와야 합니다.
        submissions = submission_crud.get_by_user_and_quiz(
            db=db, user_id=current_user.id, quiz_id=quiz_id, skip=skip, limit=limit
        )
    
    return submissions


@router.get("/{quiz_id}/submissions/{submission_id}", response_model=SubmissionWithDetails)
def read_submission(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    특정 응시 기록을 ID로 조회합니다.
    """
    submission = submission_crud.get_by_quiz_and_submission_id(
        db=db, quiz_id=quiz_id, submission_id=submission_id
    )
    if not submission:
        raise HTTPException(
            status_code=404,
            detail="응시 기록을 찾을 수 없습니다."
        )

    if not current_user.is_admin and submission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="이 응시 기록에 접근할 권한이 없습니다."
        )

    quiz = submission.quiz
    questions = quiz.questions if quiz else []

    # 각 문제의 order와 선택지 order 포함하여 응답 구성
    return SubmissionWithDetails(
        id=submission.id,
        user_id=submission.user_id,
        quiz_id=submission.quiz_id,
        score=submission.score,
        is_completed=submission.is_completed,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
        answers=submission.answers or {},
        questions=[QuestionForUser.model_validate(q) for q in questions],
        question_order=[
            {"question_id": q.id, "order_index": q.order_index or 0}
            for q in questions
        ],
        option_orders={
            str(q.id): [
                {"option_id": o.id, "order_index": o.order_index or 0}
                for o in q.options
            ] for q in questions
        }
    )


# 여러 답변을 받는 API 함수
@router.put("/{quiz_id}/submissions/{submission_id}/answers", response_model=SubmissionRead)
def submit_answers(
    quiz_id: int,
    submission_id: int,
    answers_in: List[AnswerSubmit],  # 여러 개의 답을 받기 위해 리스트로 수정
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    퀴즈 응시 도중 여러 문제에 대한 답변을 제출합니다.
    """
    submission = submission_crud.get(db=db, id=submission_id)
    if not submission or submission.quiz_id != quiz_id:
        raise HTTPException(
            status_code=404,
            detail="응시 기록을 찾을 수 없습니다."
        )
    
    # 본인 응시 기록인지 확인
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="이 응시 기록을 수정할 권한이 없습니다."
        )
    
    # 이미 제출 완료된 응시 기록은 수정 불가
    if submission.is_completed:
        raise HTTPException(
            status_code=400,
            detail="이미 제출된 퀴즈는 수정할 수 없습니다."
        )
    
    # 여러 답안 저장
    submission = submission_crud.add_answers(  # 수정된 add_answers 사용
        db=db, 
        submission_id=submission_id, 
        answers_in=answers_in  # 여러 문제에 대한 답을 한 번에 전달
    )
    
    return submission


@router.put("/{quiz_id}/submissions/{submission_id}/submit", response_model=SubmissionWithDetails)
def submit_quiz(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    퀴즈 전체 응시 완료 후 제출합니다. 자동 채점도 수행됩니다.
    """
    submission = submission_crud.get(db=db, id=submission_id)
    if not submission or submission.quiz_id != quiz_id:
        raise HTTPException(
            status_code=404,
            detail="응시 기록을 찾을 수 없습니다."
        )
    
    if submission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="이 퀴즈를 제출할 권한이 없습니다."
        )
    
    if submission.is_completed:
        raise HTTPException(
            status_code=400,
            detail="이미 제출된 퀴즈입니다."
        )
    
    # 퀴즈 정보와 문제 불러오기
    quiz = get_quiz_with_questions(db=db, quiz_id=quiz_id)

    # 채점 수행
    graded_submission = grade_submission(db=db, submission=submission, quiz=quiz)
    
    # 제출 완료 처리
    update_data = {"is_completed": True, "score": graded_submission.score}
    updated_submission = submission_crud.update(
        db=db, db_obj=submission, obj_in=update_data
    )
    
    return updated_submission


@router.get("/{quiz_id}/submissions/{submission_id}/result", response_model=SubmissionWithDetails)
def get_submission_result(
    quiz_id: int,
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    퀴즈 제출 완료 후 결과를 조회합니다.
    """
    submission = submission_crud.get_with_details(db=db, id=submission_id)
    if not submission or submission.quiz_id != quiz_id:
        raise HTTPException(
            status_code=404,
            detail="응시 기록을 찾을 수 없습니다."
        )
    
    if not current_user.is_admin and submission.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="이 응시 기록에 접근할 권한이 없습니다."
        )
    
    if not submission.is_completed:
        raise HTTPException(
            status_code=400,
            detail="아직 제출되지 않은 퀴즈입니다."
        )
    
    return submission