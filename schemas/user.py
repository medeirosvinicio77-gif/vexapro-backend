from pydantic import BaseModel, EmailStr
from typing import Optional

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class UserRead(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}