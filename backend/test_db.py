import traceback
def test():
    try:
        from app.db.database import SessionLocal
        from app.models.resume import Resume
        db = SessionLocal()
        db.query(Resume).first()
        print("Success")
    except Exception as e:
        with open("error.txt", "w") as f:
            f.write(traceback.format_exc())

test()
