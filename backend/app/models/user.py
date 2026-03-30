from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=False, default="User")
    hashed_password = Column(String, nullable=False)
    is_guest = Column(Boolean, default=False)
    ai_model = Column(String, nullable=True)
    ai_language = Column(String, nullable=True)
    ai_voice = Column(String, nullable=True)
    ai_name = Column(String, nullable=True, default="Nova")
    created_at = Column(DateTime, default=datetime.utcnow)

    resumes = relationship("Resume", back_populates="user")
    job_applications = relationship("JobApplication", back_populates="user")
    interview_sessions = relationship("InterviewSession", back_populates="user")
    chat_sessions = relationship("ChatSession", back_populates="user")
    linkedin_profile = relationship("LinkedInProfile", back_populates="user", uselist=False)
