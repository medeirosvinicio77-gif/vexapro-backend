from uuid import UUID
from typing import List
from sqlalchemy.orm import Session
from models.measurement import Measurement
from repositories.base_repository import BaseRepository

class MeasurementRepository(BaseRepository[Measurement]):
    def __init__(self, session: Session):
        super().__init__(Measurement, session)

    def get_by_video(self, video_id: UUID) -> List[Measurement]:
        return (
            self.session.query(self.model)
            .filter(self.model.video_id == video_id)
            .all()
        )