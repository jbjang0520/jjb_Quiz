from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.base import Base

# 제네릭 타입 선언
ModelType = TypeVar("ModelType", bound=Base)  # SQLAlchemy 모델
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # 생성 시 사용되는 Pydantic 스키마
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # 업데이트 시 사용되는 Pydantic 스키마

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUDBase 초기화 함수

        Args:
            model: SQLAlchemy 모델 클래스
        """
        self.model = model

    def get(self, db: Session, id: int) -> Optional[ModelType]:
        """
        ID로 단일 객체를 조회합니다.

        Args:
            db: DB 세션
            id: 조회할 객체의 ID

        Returns:
            조회된 객체 또는 None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        여러 객체를 페이징하여 조회합니다.

        Args:
            db: DB 세션
            skip: 건너뛸 항목 수
            limit: 가져올 최대 항목 수

        Returns:
            객체 리스트
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        새로운 객체를 생성합니다.

        Args:
            db: DB 세션
            obj_in: 생성할 데이터(Pydantic 스키마)

        Returns:
            생성된 DB 객체
        """
        obj_in_data = jsonable_encoder(obj_in)  # JSON 직렬화 가능한 형태로 변환
        db_obj = self.model(**obj_in_data)     # 모델 인스턴스 생성
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)  # DB로부터 새로고침하여 ID 등 반영
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        기존 객체를 업데이트합니다.

        Args:
            db: DB 세션
            db_obj: 기존 DB 객체
            obj_in: 업데이트할 데이터(Pydantic 또는 dict)

        Returns:
            업데이트된 DB 객체
        """
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])  # 해당 필드 업데이트

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        객체를 삭제합니다.

        Args:
            db: DB 세션
            id: 삭제할 객체의 ID

        Returns:
            삭제된 객체
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj