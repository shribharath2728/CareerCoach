import traceback
import sys
import os

sys.path.append(os.path.dirname(__file__))

def test():
    try:
        from app.db.database import Base, engine
        from app.models.user import User
        from app.models.chat import ChatSession, ChatMessage
        from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
        from app.models.job import JobApplication
        from app.models.resume import Resume
        from app.models.linkedin import LinkedInProfile

        print("Models imported. Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")

        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")

    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test()
