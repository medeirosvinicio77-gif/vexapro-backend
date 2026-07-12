from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from database.database import Base
import uuid
from datetime import datetime

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    room_type = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    
    width_meters = Column(Float, nullable=True)
    depth_meters = Column(Float, nullable=True)
    height_meters = Column(Float, nullable=True)
    area_m2 = Column(Float, nullable=True)
    
    status = Column(String(50), default="pending")
    scale_factor = Column(Float, nullable=True)
    camera_matrix = Column(JSON, nullable=True)
    dist_coeffs = Column(JSON, nullable=True)
    
    floor_plan_url = Column(String(500), nullable=True)
    point_cloud_url = Column(String(500), nullable=True)
    
    selected_products = Column(JSON, nullable=True)
    wall_color = Column(String(50), nullable=True)
    floor_type = Column(String(100), nullable=True)
    total_budget = Column(Float, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")