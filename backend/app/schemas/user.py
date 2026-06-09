from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import datetime

class UserCreate(BaseModel):
    full_name: str = "User"
    email: EmailStr
    password: str = ""
    is_guest: bool = False
    theme: str = "dark"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdateSettings(BaseModel):
    ai_name: Optional[str] = None
    ai_model: Optional[str] = None
    ai_language: Optional[str] = None
    ai_voice: Optional[str] = None
    theme: Optional[str] = None
    field_of_study: Optional[str] = None
    education_level: Optional[str] = None
    coaching_style: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    is_guest: bool
    ai_name: Optional[str] = None
    ai_model: Optional[str] = None
    ai_language: Optional[str] = None
    ai_voice: Optional[str] = None
    theme: str = "dark"
    field_of_study: Optional[str] = None
    education_level: Optional[str] = None
    coaching_style: Optional[str] = "supportive"
    streak_count: Optional[int] = 0
    last_practice_date: Optional[str] = None

    @field_validator('last_practice_date', mode='before')
    @classmethod
    def coerce_date_to_str(cls, v):
        if isinstance(v, (datetime.date, datetime.datetime)):
            return v.isoformat()
        return v

    class Config:
        from_attributes = True
