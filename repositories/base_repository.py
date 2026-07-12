from typing import TypeVar, Generic, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")

class BaseRepository(Generic[ModelType]):
    def __init__(self, model, session: Session):
        self.model = model
        self.session = session

    def get(self, id: UUID) -> Optional[ModelType]:
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.session.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        self.session.add(db_obj)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, update_data: dict) -> ModelType:
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        self.session.commit()
        self.session.refresh(db_obj)
        return db_obj

    def delete(self, id: UUID) -> Optional[ModelType]:
        db_obj = self.get(id)
        if db_obj:
            self.session.delete(db_obj)
            self.session.commit()
        return db_obj