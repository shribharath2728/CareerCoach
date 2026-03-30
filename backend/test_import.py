import sys
import traceback

try:
    import app.main
    print("Import OK")
except Exception as e:
    print(f"Import FAILED: {e}")
    traceback.print_exc()
