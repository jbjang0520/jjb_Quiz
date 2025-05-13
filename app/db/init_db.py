import logging
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.crud import user as user_crud_module
from app.models.base import Base
from app.db.session import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    """
    데이터베이스 초기화 및 기본 관리자 계정 생성
    """
    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 기본 관리자 계정 생성
    admin_user = crud.user.get_by_email(db, email="admin@example.com")
    if not admin_user:
        user_in = schemas.UserCreate(
            email="admin@example.com",
            password="admin",
        )
        admin_user = user_crud.create(db, obj_in=user_in)
        # 관리자 권한 부여
        admin_user.is_admin = True
        db.add(admin_user)
        db.commit()
        logger.info("Admin user created")
    else:
        logger.info("Admin user already exists")