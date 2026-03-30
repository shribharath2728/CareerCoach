from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserCreate(BaseModel):
    full_name: str = "User"
    email: EmailStr
    password: str = ""
    is_guest: bool = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdateSettings(BaseModel):
    ai_name: Optional[str] = None
    ai_model: Optional[str] = None
    ai_language: Optional[str] = None
    ai_voice: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_guest: bool
    ai_name: Optional[str] = None
    ai_model: Optional[str] = None
    ai_language: Optional[str] = None
    ai_voice: Optional[str] = None

    class Config:
        from_attributes = True
