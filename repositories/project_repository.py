from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from models.project import Project
from repositories.base_repository import BaseRepository

class ProjectRepository(BaseRepository[Project]):
    def __init__(self, session: Session):
        super().__init__(Project, session)

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Project]:
        return (
            self.session.query(self.model)
            .filter(self.model.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )