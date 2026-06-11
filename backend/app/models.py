# app/models.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    access_token: str
    refresh_token: str
    new_password: str

class RefreshSessionRequest(BaseModel):
    refresh_token: str

class UsageLog(BaseModel):
    user_id: str
    tokens_in: int
    tokens_out: int
    cost_credits: float
    book_id: Optional[str] = None
    timestamp: datetime

class SignUpMsg(BaseModel):
    message: str
