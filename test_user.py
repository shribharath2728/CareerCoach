import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, "backend")
sys.path.insert(0, backend_dir)

from app.db.database import SessionLocal
from app.services.user_service import create_user_service
from app.schemas.user import UserCreate

def test():
    db = SessionLocal()
    try:
        user = create_user_service(db, UserCreate(
            full_name="Guest 1234",
            email="guest1234@example.com",
            password="",
            is_guest=True
        ))
        print("Success! Created user id:", user.id)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
