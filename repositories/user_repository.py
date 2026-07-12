from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from models.user import User
from repositories.base_repository import BaseRepository

class UserRepository(BaseRepository[User]):
    def __init__(self, session: Session):
        super().__init__(User, session)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.session.query(self.model).filter(self.model.email == email).first()