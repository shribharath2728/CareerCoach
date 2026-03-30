from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumeUpsert(BaseModel):
    user_id: int
    content: str
    title: Optional[str] = "My Resume"

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class JDAnalyzeRequest(BaseModel):
    jd_text: str
