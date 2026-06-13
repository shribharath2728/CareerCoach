import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env regardless of current working directory
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND_ROOT / ".env")
load_dotenv()

class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./career.db")
    groq_api_key: str | None = os.getenv("GROQ_API_KEY")
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    web_fetcher_timeout_seconds: int = int(os.getenv("WEB_FETCHER_TIMEOUT_SECONDS", "10"))

settings = Settings()
