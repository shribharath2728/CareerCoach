import psycopg2

def fix_schema():
    try:
        conn = psycopg2.connect("postgresql://postgres:shri01@localhost:5432/career_assistant_db")
        cur = conn.cursor()
        
        commands = [
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR DEFAULT 'User'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_guest BOOLEAN DEFAULT FALSE",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_model VARCHAR",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_language VARCHAR",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_voice VARCHAR",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_name VARCHAR DEFAULT 'Nova'",
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"
        ]
        
        for cmd in commands:
            print(f"Executing: {cmd}")
            cur.execute(cmd)
            
        conn.commit()
        print("Schema update successful.")
        
        # Verify columns
        cur.execute("SELECT * FROM users LIMIT 0")
        colnames = [desc[0] for desc in cur.description]
        print(f"Current columns in users: {', '.join(colnames)}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fix_schema()
