from fastapi import APIRouter, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from models.user import User
from api.deps import get_current_user
from services.pipeline_completo import PipelineCompleto
import os
import json

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.post("/processar/{project_id}")
async def processar_video(
    project_id: str,
    video_path: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processa um vídeo e retorna as medidas reais das paredes"""
    
    # Se não informou caminho, buscar o vídeo mais recente do projeto
    if not video_path:
        uploads_dir = f"uploads/{project_id}"
        if os.path.exists(uploads_dir):
            videos = [f for f in os.listdir(uploads_dir) if os.path.isfile(os.path.join(uploads_dir, f))]
            if videos:
                video_path = os.path.join(uploads_dir, videos[-1])
    
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Vídeo não encontrado. Faça upload primeiro.")
    
    pipeline = PipelineCompleto(video_path, project_id)
    resultado = pipeline.executar()
    
    return {
        "status": "success",
        "resultado": resultado
    }

@router.get("/resultado/{project_id}")
async def obter_resultado(project_id: str):
    """Retorna o resultado do processamento"""
    resultado_path = f"outputs/{project_id}/resultado_final.json"
    
    if os.path.exists(resultado_path):
        with open(resultado_path, "r") as f:
            return json.load(f)
    
    return {
        "status": "nao_encontrado",
        "message": "Processe um vídeo primeiro usando POST /pipeline/processar/{project_id}"
    }

@router.get("/paredes/{project_id}")
async def obter_paredes(project_id: str):
    """Retorna apenas as informações das paredes detectadas"""
    resultado_path = f"outputs/{project_id}/resultado_final.json"
    
    if os.path.exists(resultado_path):
        with open(resultado_path, "r") as f:
            data = json.load(f)
        return data.get("paredes", {"total_paredes": 0})
    
    paredes_path = f"outputs/{project_id}/paredes.json"
    if os.path.exists(paredes_path):
        with open(paredes_path, "r") as f:
            return json.load(f)
    
    return {
        "total_paredes": 0,
        "paredes": [],
        "aviso": "Nenhum dado encontrado. Processe um vídeo primeiro."
    }