import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# Default when env / DB has no model set
DEFAULT_CHAT_MODEL = "llama-3.3-70b-versatile"

DEPRECATED_GROQ_MODELS: Dict[str, str] = {
    "mixtral-8x7b-32768": DEFAULT_CHAT_MODEL,
    "llama3-70b-8192": DEFAULT_CHAT_MODEL,
    "llama3-8b-8192": "llama-3.1-8b-instant",
    "gemma-7b-it": DEFAULT_CHAT_MODEL,
    "gemma2-9b-it": DEFAULT_CHAT_MODEL,
}

def resolve_groq_model(requested: str | None) -> str:
    if not requested or not str(requested).strip():
        return os.getenv("GROQ_MODEL", DEFAULT_CHAT_MODEL)
    r = str(requested).strip()
    if r in DEPRECATED_GROQ_MODELS:
        resolved = DEPRECATED_GROQ_MODELS[r]
        logger.info("Remapping deprecated Groq model %r -> %r", r, resolved)
        return resolved
    return r
