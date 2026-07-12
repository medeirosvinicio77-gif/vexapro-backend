from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database.database import Base
import uuid
from datetime import datetime

class Measurement(Base):
    __tablename__ = "measurements"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    video_id = Column(String(36), ForeignKey("videos.id"), nullable=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    
    measurement_type = Column(String(100), nullable=False)
    method = Column(String(50), nullable=False)
    
    value_meters = Column(Float, nullable=False)
    unit = Column(String(10), default="m")
    confidence = Column(Float, nullable=True)
    
    point1 = Column(JSON, nullable=True)
    point2 = Column(JSON, nullable=True)
    
    reference_object = Column(String(100), nullable=True)
    reference_value = Column(Float, nullable=True)
    
    width_meters = Column(Float, nullable=True)
    height_meters = Column(Float, nullable=True)
    area_m2 = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    video = relationship("Video", back_populates="measurements")