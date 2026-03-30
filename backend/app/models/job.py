from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_name = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    application_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Applied")
    notes = Column(Text)
    linkedin_job_url = Column(String)

    user = relationship("User", back_populates="job_applications")
    interview_sessions = relationship("InterviewSession", back_populates="job_application")
