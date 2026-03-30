import traceback
def test():
    try:
        from app.core.database import Base, engine
        from app.models.job import JobApplication
        from app.models.resume import Resume
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        Base.metadata.create_all(bind=engine)
        print("Success")
    except Exception as e:
        with open("error.txt", "w") as f:
            f.write(traceback.format_exc())

test()
