import sys
import traceback

try:
    from sqlalchemy import create_engine
    from sqlalchemy import inspect
    # We load from .env usually, let's just parse it manually
    import os
    env_path = os.path.join(os.path.dirname(__file__), "backend", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for l in f:
                if l.startswith("DATABASE_URL="):
                    url = l.split("=", 1)[1].strip()
                    engine = create_engine(url)
                    inspector = inspect(engine)
                    columns = inspector.get_columns("users")
                    cols = [c["name"] for c in columns]
                    with open("cols.txt", "w") as out:
                        out.write(",".join(cols))
                    print("Found columns:", cols)
                    break
except Exception as e:
    with open("cols.txt", "w") as out:
        out.write("ERROR: " + str(e))
    traceback.print_exc()
