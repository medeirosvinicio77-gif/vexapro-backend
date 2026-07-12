from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}