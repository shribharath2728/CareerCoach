import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")
sys.path.insert(0, backend_dir)

from app.core.database import SessionLocal
from sqlalchemy import text

def run():
    db = SessionLocal()
    try:
        # Check if columns exist
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_model VARCHAR(255) DEFAULT 'llama-3.3-70b-versatile';"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_language VARCHAR(50) DEFAULT 'en-US';"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_voice VARCHAR(255) DEFAULT '';"))
        db.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE;"))
        db.commit()
        print("MIGRATION SUCCESSFUL! Columns added.", flush=True)
        with open("migration_result.txt", "w") as f:
            f.write("Migration successful.")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"FAILED: {e}", flush=True)
        with open("migration_result.txt", "w") as f:
            f.write(f"Migration failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    run()
