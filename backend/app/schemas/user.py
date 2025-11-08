from pydantic import BaseModel, EmailStr
from typing import Optional
from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_id: str
    role: Optional[UserRole] = UserRole.reviewer


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: str
    is_active: bool
    
    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: str

