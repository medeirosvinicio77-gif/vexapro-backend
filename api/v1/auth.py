from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional

from database.database import get_db
from models.user import User
from core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

# Schemas
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    role: Optional[str] = "client"  # client, professional

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True

# ============ LOGIN ============

@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login com email e senha
    Retorna tokens JWT e dados do usuário
    """
    # Buscar usuário pelo email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário inativo. Entre em contato com o suporte."
        )
    
    # Atualizar último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Gerar tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_verified": user.is_verified
        }
    }

# ============ REGISTRO ============

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Registra um novo usuário (PF ou Profissional)
    """
    # Verificar se email já existe
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Validar role
    if data.role not in ["client", "professional"]:
        data.role = "client"
    
    # Criar usuário
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        name=data.name or data.email.split("@")[0],
        role=data.role,
        is_verified=True  # Auto-verificar por enquanto
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Gerar tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "message": "Conta criada com sucesso!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "is_verified": user.is_verified
        }
    }

# ============ REFRESH TOKEN ============

@router.post("/refresh")
def refresh_token(
    data: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Renova o access token usando o refresh token
    """
    payload = decode_token(data.refresh_token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado"
        )
    
    # Gerar novos tokens
    access_token = create_access_token(subject=user.id)
    new_refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

# ============ PERFIL ============

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    """Retorna o perfil do usuário logado"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "phone": current_user.phone,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "created_at": str(current_user.created_at),
        "last_login": str(current_user.last_login) if current_user.last_login else None
    }

@router.put("/me")
def update_profile(
    name: Optional[str] = None,
    phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza o perfil do usuário"""
    if name:
        current_user.name = name
    if phone:
        current_user.phone = phone
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "Perfil atualizado com sucesso!"}

@router.put("/change-password")
def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Altera a senha do usuário"""
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Senha alterada com sucesso!"}

# ============ ADMIN ============

@router.get("/users")
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lista todos os usuários (admin)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": str(u.created_at)
        }
        for u in users
    ]