from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class LinkedInProfile(Base):
    __tablename__ = "linkedin_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    profile_url = Column(String, nullable=False)
    headline = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    summary = Column(Text)
    experience = Column(Text)
    education = Column(Text)
    skills = Column(Text)

    user = relationship("User", back_populates="linkedin_profile")
