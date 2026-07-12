from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class VideoCreate(BaseModel):
    project_id: str
    filename: str
    file_size: int
    duration: Optional[float] = None

class VideoRead(BaseModel):
    id: str
    project_id: str
    filename: str
    file_size: int
    duration: Optional[float] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}