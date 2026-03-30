from pydantic import BaseModel, computed_field
from typing import Optional
from datetime import datetime

class JobApplicationCreate(BaseModel):
    user_id: int
    company: str
    role: str
    status: Optional[str] = "Applied"
    notes: Optional[str] = None
    linkedin_job_url: Optional[str] = None

class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    linkedin_job_url: Optional[str] = None

class JobApplicationResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    job_title: str
    application_date: datetime
    status: Optional[str] = "Applied"
    notes: Optional[str] = None
    linkedin_job_url: Optional[str] = None

    class Config:
        from_attributes = True

    @computed_field
    def company(self) -> str:
        return self.company_name

    @computed_field
    def role(self) -> str:
        return self.job_title
