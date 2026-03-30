import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env regardless of current working directory (e.g. uvicorn from repo root)
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv()

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./career.db")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")

settings = Settings()
