
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def inspect_db():
    with open("db_inspect_log.txt", "w") as f:
        f.write("Starting inspection...\n")
        DATABASE_URL = os.getenv("DATABASE_URL")
        f.write(f"Connecting to: {DATABASE_URL}\n")
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # List all tables
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = cur.fetchall()
            f.write(f"Tables: {tables}\n")

            # For each table, list columns
            for table in tables:
                t_name = table[0]
                cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{t_name}';")
                cols = cur.fetchall()
                f.write(f"Table '{t_name}' columns: {cols}\n")

            cur.close()
            conn.close()
        except Exception as e:
            f.write(f"Error during inspection: {e}\n")

if __name__ == "__main__":
    inspect_db()
