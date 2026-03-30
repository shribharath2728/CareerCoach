import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageOut,
    ChatTurnResponse,
)
from app.services.chat_service import (
    get_chat_sessions,
    create_chat_session,
    send_message,
    get_ai_response,
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/sessions/{user_id}", response_model=list[ChatSessionResponse])
def get_user_chat_sessions(user_id: int, db: Session = Depends(get_db)):
    return get_chat_sessions(user_id, db)

@router.post("/sessions", response_model=ChatSessionResponse)
def create_new_chat_session(session: ChatSessionCreate, db: Session = Depends(get_db)):
    return create_chat_session(session.user_id, db, session_name=session.session_name)

@router.get("/messages/{session_id}", response_model=list[ChatMessageOut])
def list_messages(session_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    return [ChatMessageOut.from_row(r) for r in rows]

@router.post("/messages", response_model=ChatTurnResponse)
def send_chat_message(message: ChatMessageCreate, db: Session = Depends(get_db)):
    if not message.content or not str(message.content).strip():
        raise HTTPException(status_code=400, detail="Message content is required")

    sess = db.query(ChatSession).filter(ChatSession.id == message.session_id).first()
    if not sess:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session {message.session_id} not found. Create one with POST /chat/sessions first.",
        )

    role = message.role if message.role in ("user", "assistant") else "user"
    try:
        user_msg = send_message(message.session_id, role, message.content.strip(), db)
    except SQLAlchemyError as e:
        logger.exception("Failed to save user message")
        raise HTTPException(
            status_code=500,
            detail=f"Database error saving message: {e!s}",
        ) from e
    user = db.query(User).filter(User.id == sess.user_id).first()
    model_hint = user.ai_model if user else None

    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == message.session_id)
        .order_by(ChatMessage.timestamp)
        .all()
    )
    message_list = [
        {"role": m.role or "user", "content": (m.content if m.content is not None else "")}
        for m in rows
    ]

    try:
        ai_content = get_ai_response(message_list, model_hint=model_hint)
    except Exception as e:
        logger.exception("Groq/OpenAI chat completion failed")
        raise HTTPException(
            status_code=502,
            detail=f"AI service error: {e!s}. Check GROQ_API_KEY / GROQ_BASE_URL and model name.",
        ) from e

    try:
        ai_msg = send_message(message.session_id, "assistant", ai_content, db)
    except SQLAlchemyError as e:
        logger.exception("Failed to save assistant message")
        raise HTTPException(
            status_code=500,
            detail=f"Database error saving reply: {e!s}",
        ) from e

    # Re-load rows after commits so response serialization never sees stale/expired ORM state
    uid, aid = user_msg.id, ai_msg.id
    u_row = db.get(ChatMessage, uid)
    a_row = db.get(ChatMessage, aid)
    if not u_row or not a_row:
        logger.error("Messages missing after insert: user=%s assistant=%s", uid, aid)
        raise HTTPException(status_code=500, detail="Messages could not be reloaded after save.")

    return ChatTurnResponse(
        user_message=ChatMessageOut.from_row(u_row),
        assistant_message=ChatMessageOut.from_row(a_row),
    )
