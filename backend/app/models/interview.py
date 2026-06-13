from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import JSONB

from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_application_id = Column(Integer, ForeignKey("job_applications.id"), nullable=True)
    session_date = Column(DateTime, default=datetime.utcnow)
    overall_feedback = Column(Text)
    score = Column(Integer)
    role = Column(String, nullable=True)
    interview_type = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    field_of_study = Column(String, nullable=True) # Context at session start

    user = relationship("User", back_populates="interview_sessions")
    job_application = relationship("JobApplication", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session")

class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    expected_answer = Column(Text)
    user_answer = Column(Text)
    feedback = Column(Text)
    score = Column(Integer)
    category = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    question_order = Column(Integer, default=1, nullable=False)
    expected_answer_points = Column(JSONB, nullable=True)

    session = relationship("InterviewSession", back_populates="questions")
    answers = relationship("InterviewAnswer", back_populates="question")

class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("interview_questions.id"), nullable=False)
    answer_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)

    question = relationship("InterviewQuestion", back_populates="answers")
