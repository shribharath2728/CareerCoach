
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def fix_db():
    print("Starting migration...")
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Try to construct from components if missing
        db_user = os.getenv("POSTGRES_USER", "postgres")
        db_pass = os.getenv("POSTGRES_PASSWORD", "postgres")
        db_host = os.getenv("POSTGRES_HOST", "localhost")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "career_assistant")
        DATABASE_URL = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        def _add_col(table, col, col_type):
            cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND column_name = '{col}';")
            if not cur.fetchone():
                print(f"Adding column {table}.{col}...")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type};")
            else:
                print(f"Column {table}.{col} already exists.")

        # Ensure users table has all columns
        _add_col("users", "full_name", "VARCHAR DEFAULT 'User'")
        _add_col("users", "hashed_password", "VARCHAR")
        _add_col("users", "is_guest", "BOOLEAN DEFAULT FALSE")
        _add_col("users", "ai_model", "VARCHAR")
        _add_col("users", "ai_language", "VARCHAR")
        _add_col("users", "ai_voice", "VARCHAR")
        _add_col("users", "ai_name", "VARCHAR DEFAULT 'Nova'")
        _add_col("users", "created_at", "TIMESTAMP DEFAULT NOW()")

        # Handle legacy rename if applicable
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_hash';")
        if cur.fetchone():
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'hashed_password';")
            if not cur.fetchone():
                print("Renaming users.password_hash -> hashed_password")
                cur.execute("ALTER TABLE users RENAME COLUMN password_hash TO hashed_password;")

        # Ensure interview_sessions table has all columns
        _add_col("interview_sessions", "role", "VARCHAR")
        _add_col("interview_sessions", "interview_type", "VARCHAR")
        _add_col("interview_sessions", "difficulty", "VARCHAR")
        _add_col("interview_sessions", "session_date", "TIMESTAMP DEFAULT NOW()")
        _add_col("interview_sessions", "overall_feedback", "TEXT")
        _add_col("interview_sessions", "score", "INTEGER")
        _add_col("interview_sessions", "job_application_id", "INTEGER")

        # Ensure interview_questions table has all columns
        _add_col("interview_questions", "category", "VARCHAR")
        _add_col("interview_questions", "difficulty", "VARCHAR")
        _add_col("interview_questions", "expected_answer", "TEXT")
        _add_col("interview_questions", "user_answer", "TEXT")
        _add_col("interview_questions", "feedback", "TEXT")
        _add_col("interview_questions", "score", "INTEGER")
        _add_col("interview_questions", "question_order", "INTEGER NOT NULL DEFAULT 1")
        _add_col("interview_questions", "expected_answer_points", "JSONB")

        # Ensure interview_answers table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS interview_answers (
                id SERIAL PRIMARY KEY,
                question_id INTEGER NOT NULL REFERENCES interview_questions(id),
                answer_text TEXT NOT NULL
            );
        """)
        _add_col("interview_answers", "is_correct", "BOOLEAN DEFAULT FALSE")
        print("Ensured table interview_answers exists with all columns.")

        # Ensure chat_sessions table has all columns
        _add_col("chat_sessions", "title", "VARCHAR")

        print("Database migration complete.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    fix_db()
