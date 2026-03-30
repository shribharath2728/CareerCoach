
import os
from sqlalchemy import create_engine, inspect, text
from app.db.database import Base
from app.models import user, resume, job, interview, chat, linkedin
from dotenv import load_dotenv

load_dotenv()

def migrate():
    url = os.getenv("DATABASE_URL")
    print(f"URL: {url}")
    engine = create_engine(url)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("MetaData.create_all executed.")
    
    # Direct check and add missing columns for interview_answers
    with engine.connect() as conn:
        # Check if column is_correct exists in interview_answers
        insp = inspect(engine)
        if "interview_answers" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("interview_answers")}
            if "is_correct" not in cols:
                conn.execute(text("ALTER TABLE interview_answers ADD COLUMN is_correct BOOLEAN DEFAULT FALSE"))
                print("Column is_correct added to interview_answers.")
            else:
                print("Column is_correct already exists.")
        else:
            print("interview_answers table was not found even after create_all!")
            
    print("Migration finished.")

if __name__ == "__main__":
    migrate()
