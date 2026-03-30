
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def run():
    url = os.getenv("DATABASE_URL")
    print(f"URL: {url}")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        print("Connected.")
        
        cur.execute("ALTER TABLE interview_answers ADD COLUMN IF NOT EXISTS is_correct BOOLEAN DEFAULT FALSE;")
        print("Column is_correct ensured.")
        
        cur.close()
        conn.close()
        print("Done.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    run()
