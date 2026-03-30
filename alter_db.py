import os
import sys

# Add the project directory to sys.path so we can import app modules
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from app.core.config import settings
import traceback

def main():
    print("Connecting to database:", settings.DATABASE_URL)
    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        try:
            # Check if columns exist
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users';"))
            columns = [row[0] for row in result]
            
            if 'password_hash' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);"))
                print("Added password_hash column to users.")
                
            if 'ai_model' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN ai_model VARCHAR(255) DEFAULT 'llama-3.3-70b-versatile';"))
                print("Added ai_model column to users.")
                
            if 'ai_language' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN ai_language VARCHAR(50) DEFAULT 'en-US';"))
                print("Added ai_language column to users.")
                
            if 'ai_voice' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN ai_voice VARCHAR(255) DEFAULT '';"))
                print("Added ai_voice column to users.")

            if 'is_guest' not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_guest BOOLEAN DEFAULT FALSE;"))
                print("Added is_guest column to users.")

            conn.commit()
            print("Successfully updated database schema.")
        except Exception as e:
            print("Error updating schema:", e)
            traceback.print_exc()

if __name__ == "__main__":
    main()
