from fastapi import APIRouter, Depends
from api.deps import get_current_user
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def list_users(current_user: User = Depends(get_current_user)):
    return {"users": [], "message": "Use /auth/users para listar"}

@router.get("/me")
def current_user_info(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role
    }