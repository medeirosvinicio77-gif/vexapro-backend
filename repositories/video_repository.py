from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from models.video import Video
from repositories.base_repository import BaseRepository

class VideoRepository(BaseRepository[Video]):
    def __init__(self, session: Session):
        super().__init__(Video, session)

    def get_by_project(self, project_id: UUID) -> List[Video]:
        return (
            self.session.query(self.model)
            .filter(self.model.project_id == project_id)
            .all()
        )