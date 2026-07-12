from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from database.database import Base
import uuid
from datetime import datetime

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=True)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Float, nullable=True)
    
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    
    duration_seconds = Column(Float, nullable=True)
    fps = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    
    status = Column(String(50), default="pending")
    frames_extracted = Column(Integer, nullable=True)
    markers_detected = Column(Integer, nullable=True)
    
    scale_factor = Column(Float, nullable=True)
    camera_matrix = Column(JSON, nullable=True)
    dist_coeffs = Column(JSON, nullable=True)
    control_points = Column(JSON, nullable=True)
    
    output_dir = Column(String(500), nullable=True)
    point_cloud_path = Column(String(500), nullable=True)
    floor_plan_path = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    project = relationship("Project", back_populates="videos")
    measurements = relationship("Measurement", back_populates="video", cascade="all, delete-orphan")