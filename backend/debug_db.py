
import os
from sqlalchemy import create_engine, text
from app.db.database import Base
from app.models import user, resume, job, interview, chat, linkedin
from dotenv import load_dotenv

load_dotenv()

def check():
    url = os.getenv("DATABASE_URL")
    print(f"URL: {url}")
    engine = create_engine(url)
    
    # Create all
    Base.metadata.create_all(bind=engine)
    print("MetaData.create_all done.")
    
    with engine.connect() as conn:
        res = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
        tabs = [r[0] for r in res]
        print(f"Tables: {tabs}")
        
if __name__ == "__main__":
    check()
