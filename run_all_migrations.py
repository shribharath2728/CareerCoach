import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import Base, engine
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.models.interview_evaluation import Evaluation
from app.models.job import JobApplication
from app.models.resume import Resume

print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Done!")
