from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Any:
    """
    현재 로그인한 사용자 정보를 가져옵니다.
    """
    return current_user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    자신의 사용자 정보를 업데이트합니다.
    """
    # 일반 사용자는 자신의 관리자 권한을 변경할 수 없음
    if user_in.is_admin is not None:
        if not crud.user.is_admin(current_user):
            user_in.is_admin = current_user.is_admin

    user = crud.user.update(db, db_obj=current_user, obj_in=user_in)
    return user

@router.get("/", response_model=List[schemas.User])
def read_users(
    db: Session = Depends(deps.get_db),
    pagination: Dict[str, int] = Depends(deps.get_pagination_params),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    사용자 목록을 조회합니다. 관리자만 접근 가능합니다.
    """
    users = crud.user.get_multi(db, **pagination)
    return users

@router.post("/", response_model=schemas.User)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_admin_user),
) -> Any:
    """
    새 사용자를 생성합니다. 관리자만 접근 가능합니다.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="해당 이메일을 가진 사용자가 이미 존재합니다.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user