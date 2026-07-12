from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
import threading
import json
import uuid
from datetime import datetime

from database.database import get_db
from models.video import Video
from models.project import Project
from models.user import User
from api.deps import get_current_user

router = APIRouter(prefix="/videos", tags=["videos"])

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

processing_status = {}

def process_video(video_path: str, project_id: str, video_id: str, db_session_factory):
    """Processa o vídeo em background e atualiza o banco"""
    db = db_session_factory()
    
    try:
        processing_status[video_id] = "processing"
        
        # Atualizar status no banco
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = "processing"
            db.commit()
        
        import cv2
        
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Criar pasta de saída
        output_path = os.path.join(OUTPUT_DIR, project_id)
        frames_path = os.path.join(output_path, "frames")
        os.makedirs(frames_path, exist_ok=True)
        
        # Extrair frames
        frame_interval = int(fps)
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                frame_path = os.path.join(frames_path, f"frame_{saved_count:04d}.jpg")
                cv2.imwrite(frame_path, frame)
                saved_count += 1
            
            frame_count += 1
        
        cap.release()
        
        # Atualizar banco com resultados
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = "completed"
            video.duration_seconds = round(duration, 1)
            video.fps = round(fps, 1)
            video.width = width
            video.height = height
            video.frames_extracted = saved_count
            video.output_dir = output_path
            video.processed_at = datetime.utcnow()
            db.commit()
        
        processing_status[video_id] = "completed"
        print(f"✅ Processamento concluído: {saved_count} frames de {video_id}")
        
    except Exception as e:
        processing_status[video_id] = f"error: {str(e)}"
        video = db.query(Video).filter(Video.id == video_id).first()
        if video:
            video.status = "failed"
            db.commit()
        print(f"❌ Erro: {e}")
    finally:
        db.close()

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    project_id: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload de vídeo e criação no banco de dados"""
    
    # Verificar se projeto existe e pertence ao usuário
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado")
    
    # Salvar arquivo
    project_dir = os.path.join(UPLOAD_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    
    file_path = os.path.join(project_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    file_size = os.path.getsize(file_path)
    
    # Criar registro no banco
    video_id = str(uuid.uuid4())
    video = Video(
        id=video_id,
        filename=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        project_id=project_id,
        status="uploaded"
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Iniciar processamento em background
    from database.database import SessionLocal
    thread = threading.Thread(
        target=process_video,
        args=(file_path, project_id, video_id, SessionLocal)
    )
    thread.start()
    
    processing_status[video_id] = "starting"
    
    return {
        "video_id": video_id,
        "filename": file.filename,
        "project_id": project_id,
        "size": file_size,
        "status": "uploaded",
        "message": "Upload concluído! Processamento iniciado em background."
    }

@router.get("/")
async def list_videos(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista vídeos do usuário/projeto"""
    query = db.query(Video).join(Project).filter(Project.user_id == current_user.id)
    
    if project_id:
        query = query.filter(Video.project_id == project_id)
    
    videos = query.order_by(Video.created_at.desc()).all()
    
    return {
        "videos": [
            {
                "id": v.id,
                "filename": v.filename,
                "project_id": v.project_id,
                "file_size": v.file_size,
                "duration_seconds": v.duration_seconds,
                "fps": v.fps,
                "width": v.width,
                "height": v.height,
                "status": v.status,
                "frames_extracted": v.frames_extracted,
                "created_at": str(v.created_at),
                "processed_at": str(v.processed_at) if v.processed_at else None
            }
            for v in videos
        ],
        "count": len(videos)
    }

@router.get("/{video_id}")
async def get_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém detalhes de um vídeo"""
    video = db.query(Video).join(Project).filter(
        Video.id == video_id,
        Project.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    
    return {
        "id": video.id,
        "filename": video.filename,
        "project_id": video.project_id,
        "file_size": video.file_size,
        "duration_seconds": video.duration_seconds,
        "fps": video.fps,
        "width": video.width,
        "height": video.height,
        "status": video.status,
        "frames_extracted": video.frames_extracted,
        "output_dir": video.output_dir,
        "created_at": str(video.created_at),
        "processed_at": str(video.processed_at) if video.processed_at else None
    }

@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta um vídeo"""
    video = db.query(Video).join(Project).filter(
        Video.id == video_id,
        Project.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    
    # Remover arquivo
    if os.path.exists(video.file_path):
        os.remove(video.file_path)
    
    # Remover do banco
    db.delete(video)
    db.commit()
    
    return {"message": "Vídeo deletado com sucesso", "video_id": video_id}

@router.get("/status/{video_id}")
async def get_status(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifica status de processamento"""
    status = processing_status.get(video_id, "unknown")
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        status = video.status
    
    return {
        "video_id": video_id,
        "status": status,
        "frames_extracted": video.frames_extracted if video else None
    }

@router.get("/frames/{project_id}")
async def list_frames(project_id: str):
    """Lista frames de um projeto"""
    frames_dir = os.path.join(OUTPUT_DIR, project_id, "frames")
    if not os.path.exists(frames_dir):
        return {"frames": [], "count": 0}
    
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    frame_urls = [f"/api/v1/videos/frame/{project_id}/{f}" for f in frames]
    
    return {"project_id": project_id, "frames": frame_urls, "count": len(frames)}

@router.get("/frame/{project_id}/{frame_name}")
async def get_frame(project_id: str, frame_name: str):
    """Retorna um frame específico"""
    frame_path = os.path.join(OUTPUT_DIR, project_id, "frames", frame_name)
    if os.path.exists(frame_path):
        return FileResponse(frame_path, media_type="image/jpeg")
    return {"error": "Frame não encontrado"}