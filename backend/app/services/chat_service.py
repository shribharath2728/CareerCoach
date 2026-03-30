import os
from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage

sys_prompt = """You are a helpful career assistant AI. Your role is to help users with their career development, job search, resume building, interview preparation, and general career advice.

Key guidelines:
- Be empathetic and supportive, especially when users seem stressed or low.
- Provide practical, actionable advice.
- Be encouraging and positive.
- If the user seems down or frustrated, acknowledge their feelings and offer encouragement.
- Keep responses concise but comprehensive.
- Use simple language.

When detecting low mood or frustration:
- Acknowledge the emotion: "I understand this can be frustrating..."
- Offer support: "I'm here to help you through this."
- Provide positive reinforcement: "You've got this!" or "Many people face this challenge."
- Suggest small steps: Break down advice into manageable actions.

Always maintain a professional yet friendly tone.
"""

def get_chat_sessions(user_id: int, db: Session):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

def create_chat_session(user_id: int, db: Session, session_name: str | None = None):
    name = session_name or "New Chat"
    session = ChatSession(user_id=user_id, session_name=name, title=name)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def send_message(session_id: int, role: str, content: str, db: Session):
    message = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        sender=role,
        message_body=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_ai_response(messages: list[dict], model_hint: str | None = None) -> str:
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        from groq import Groq
        from app.core.groq_models import resolve_groq_model

        model = resolve_groq_model(model_hint)
        base = os.getenv("GROQ_BASE_URL", "https://api.groq.com")
        client = Groq(api_key=groq_key, base_url=base)
        msgs = [{"role": "system", "content": sys_prompt}] + messages
        res = client.chat.completions.create(model=model, messages=msgs, temperature=0.4)
        return (res.choices[0].message.content or "").strip()

    oai = os.getenv("OPENAI_API_KEY")
    if not oai:
        return (
            "AI is not configured. Set GROQ_API_KEY or OPENAI_API_KEY in the backend environment "
            "(e.g. in a `.env` file next to the API)."
        )
    import openai

    client = openai.OpenAI(api_key=oai)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": sys_prompt}] + messages,
    )
    return (response.choices[0].message.content or "").strip()
