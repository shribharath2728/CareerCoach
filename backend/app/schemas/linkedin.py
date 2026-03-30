from pydantic import BaseModel
from typing import Optional

class LinkedInProfileBase(BaseModel):
    profile_url: str
    summary: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    skills: Optional[str] = None

class LinkedInProfileCreate(LinkedInProfileBase):
    pass

class LinkedInProfileResponse(LinkedInProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
