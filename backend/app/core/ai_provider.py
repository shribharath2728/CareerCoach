"""
Unified AI Provider — CareerCoach AI
======================================
Single provider: Groq (fast, free tier)

chat_complete() routes all requests through Groq.

Keys in .env:
  GROQ_API_KEY — required
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Model catalogue ───────────────────────────────────────────────────────────

GROQ_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
}

DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"

MODEL_DISPLAY: Dict[str, str] = {
    "llama-3.3-70b-versatile":                       "Llama 3.3 70B — balanced (Groq)",
    "llama-3.1-8b-instant":                          "Llama 3.1 8B — fastest (Groq)",
    "meta-llama/llama-4-scout-17b-16e-instruct":     "Llama 4 Scout — long context (Groq)",
    "meta-llama/llama-4-maverick-17b-128e-instruct": "Llama 4 Maverick — deep reasoning (Groq)",
}


def resolve_model(requested: str | None) -> tuple[str, str]:
    """
    Return (provider, model_id). Always returns ("groq", model_id).
    Falls back to DEFAULT_GROQ_MODEL for unknown/empty values.
    """
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("No AI provider configured. Set GROQ_API_KEY in .env")

    if not requested or not str(requested).strip():
        return "groq", os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)

    r = str(requested).strip()

    # Remap deprecated Groq model names
    from app.core.groq_models import DEPRECATED_GROQ_MODELS
    if r in DEPRECATED_GROQ_MODELS:
        r = DEPRECATED_GROQ_MODELS[r]

    if r in GROQ_MODELS:
        return "groq", r

    # Unknown model — fall back to default
    return "groq", os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)


# ── Public API ────────────────────────────────────────────────────────────────

def chat_complete(
    messages: List[Dict[str, str]],
    system_prompt: str = "",
    model_hint: str | None = None,
    temperature: float = 0.4,
    max_tokens: int = 2000,
) -> str:
    """
    Send a chat completion via Groq.

    Args:
        messages:      [{"role": "user"|"assistant", "content": "..."}]
                       Do NOT include a system message — use system_prompt.
        system_prompt: System instruction string.
        model_hint:    Optional model ID. Resolved automatically if None.
        temperature:   Sampling temperature.
        max_tokens:    Max response tokens.
    """
    _, model_id = resolve_model(model_hint)
    logger.debug("chat_complete: provider=groq model=%s", model_id)
    return _groq_complete(messages, system_prompt, model_id, temperature, max_tokens)


# ── Provider implementation ───────────────────────────────────────────────────

def _groq_complete(
    messages: List[Dict[str, str]],
    system_prompt: str,
    model_id: str,
    temperature: float,
    max_tokens: int,
) -> str:
    from groq import Groq
    from app.core.groq_models import DEFAULT_CHAT_MODEL

    client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com"),
    )

    msgs: List[Dict[str, str]] = []
    if system_prompt:
        msgs.append({"role": "system", "content": system_prompt})
    msgs.extend(messages)

    try:
        res = client.chat.completions.create(
            model=model_id,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return (res.choices[0].message.content or "").strip()
    except Exception as e:
        err = str(e)
        if ("model_not_found" in err or "404" in err) and model_id != DEFAULT_CHAT_MODEL:
            logger.warning("Groq model %r not found, retrying with %s", model_id, DEFAULT_CHAT_MODEL)
            res = client.chat.completions.create(
                model=DEFAULT_CHAT_MODEL,
                messages=msgs,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (res.choices[0].message.content or "").strip()
        raise


# ── Status helper ─────────────────────────────────────────────────────────────

def get_provider_status() -> Dict[str, Any]:
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    try:
        _, m = resolve_model(None)
    except RuntimeError:
        m = "none"
    return {
        "active_provider": "groq",
        "active_model": m,
        "providers": {
            "groq": {"configured": groq_ok, "default_model": DEFAULT_GROQ_MODEL},
        },
        "all_models": MODEL_DISPLAY,
    }
