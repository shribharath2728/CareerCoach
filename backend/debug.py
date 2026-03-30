import traceback
try:
    import app.main
except Exception as e:
    with open("error.txt", "w") as f:
        f.write(traceback.format_exc())
