import os
import sys

# Change to the backend directory to pick up the correct .env
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("NO DATABASE URL FOUND!")
    sys.exit(1)

engine = create_engine(db_url)

queries = [
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_model VARCHAR(255) DEFAULT 'llama-3.3-70b-versatile';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_language VARCHAR(50) DEFAULT 'en-US';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_voice VARCHAR(255) DEFAULT '';",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE;"
]

with engine.connect() as conn:
    for q in queries:
        try:
            conn.execute(text(q))
            print("Successfully executed:", q)
        except Exception as e:
            print("Skipping or failed:", q)
            print("  Reason:", e)
    conn.commit()
    print("MIGRATION COMPLETE!")
