from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MeasurementRead(BaseModel):
    id: str
    video_id: str
    type: str
    value: float
    unit: str
    confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}