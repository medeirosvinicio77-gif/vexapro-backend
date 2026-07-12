from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from database.database import get_db
from models.project import Project
from models.user import User
from api.deps import get_current_user
import uuid

router = APIRouter(prefix="/projects", tags=["projects"])

# ============ Schemas ============

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    room_type: Optional[str] = None
    address: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    room_type: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    room_type: Optional[str]
    address: Optional[str]
    status: str
    width_meters: Optional[float]
    depth_meters: Optional[float]
    height_meters: Optional[float]
    area_m2: Optional[float]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# ============ CRUD ============

@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cria um novo projeto"""
    project = Project(
        id=str(uuid.uuid4()),
        name=data.name,
        description=data.description,
        room_type=data.room_type,
        address=data.address,
        user_id=current_user.id,
        status="active"
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "room_type": project.room_type,
        "address": project.address,
        "status": project.status,
        "width_meters": project.width_meters,
        "depth_meters": project.depth_meters,
        "height_meters": project.height_meters,
        "area_m2": project.area_m2,
        "created_at": str(project.created_at),
        "updated_at": str(project.updated_at)
    }

@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = None,
    room_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista projetos do usuário com filtros"""
    query = db.query(Project).filter(Project.user_id == current_user.id)
    
    if status:
        query = query.filter(Project.status == status)
    if room_type:
        query = query.filter(Project.room_type == room_type)
    
    projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "room_type": p.room_type,
            "address": p.address,
            "status": p.status,
            "width_meters": p.width_meters,
            "depth_meters": p.depth_meters,
            "height_meters": p.height_meters,
            "area_m2": p.area_m2,
            "created_at": str(p.created_at),
            "updated_at": str(p.updated_at)
        }
        for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém um projeto específico"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "room_type": project.room_type,
        "address": project.address,
        "status": project.status,
        "width_meters": project.width_meters,
        "depth_meters": project.depth_meters,
        "height_meters": project.height_meters,
        "area_m2": project.area_m2,
        "created_at": str(project.created_at),
        "updated_at": str(project.updated_at)
    }

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza um projeto"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Atualizar campos
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "room_type": project.room_type,
        "address": project.address,
        "status": project.status,
        "width_meters": project.width_meters,
        "depth_meters": project.depth_meters,
        "height_meters": project.height_meters,
        "area_m2": project.area_m2,
        "created_at": str(project.created_at),
        "updated_at": str(project.updated_at)
    }

@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta um projeto"""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    db.delete(project)
    db.commit()
    
    return {"message": "Projeto deletado com sucesso", "project_id": project_id}