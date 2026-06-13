"""
Chat service — CareerCoach AI
Uses the unified AI provider (Groq → Gemini → Claude waterfall).
Integrates RAG (Retrieval-Augmented Generation) for knowledge grounding.
"""
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.chat import ChatSession, ChatMessage
from app.core.ai_provider import chat_complete
from app.services import rag_service

logger = logging.getLogger(__name__)


def _build_system_prompt(rag_context: str = "") -> str:
    """Build the system prompt with today's date and optional RAG context injected."""
    today = datetime.now().strftime("%A, %d %B %Y")
    rag_section = ""
    if rag_context:
        rag_section = f"\n\n## RETRIEVED CAREER KNOWLEDGE\nUse this to ground your answers:\n{rag_context}\n"
        
    return f"""You are CareerCoach AI — a warm, brilliant AI mentor dedicated to helping students achieve their dreams.

## TEMPORAL AWARENESS & RAG-GROUNDED RESPONSES
Today's date is **{today}**.

Your training data has a knowledge cutoff (mid-2024), BUT you have access to **RAG-retrieved current information** from the knowledge base.

### How to Answer Questions
1. **CHECK RAG CONTEXT FIRST** — Look at the retrieved knowledge section below
2. **If RAG has the answer** — Use it! It contains current data added by admins
3. **If RAG doesn't have it** — Then acknowledge your cutoff limitation

### For Questions About Real-Time Topics
Real-time facts: government leaders, elections, recent news, stock prices, current events, etc.

**Priority: RAG > Training Data > Acknowledge Cutoff**

- If question is about CM, current leaders, elections, news → Check RAG first
- If RAG has current info → Answer using that information directly
- If RAG is empty for that topic → Then say: "My training data ends in mid-2024. I don't have reliable information about [topic] as of {today}. Please verify with current sources."

### Examples
- Q: "Who is the CM of Tamil Nadu in 2026?"
  - Check RAG → If RAG says "M.K. Stalin" → Answer: "The CM of Tamil Nadu is M.K. Stalin."
  - Check RAG → If RAG is empty → Answer: "My training data ends in mid-2024. To find the current CM, check the official Tamil Nadu government website."

- Q: "What's the stock price of TCS?"
  - Check RAG → Likely empty (stocks change daily) → Say: "I don't have real-time stock prices. Check financial websites."

### Never Do This
❌ Guess or make up facts if RAG is empty
❌ Ignore RAG when it has relevant information
❌ Pretend uncertainty when RAG clearly states facts

## WHO YOU ARE
You are NOT a rigid form or a structured questionnaire. You are a trusted mentor — like a brilliant senior friend who knows everything about tech careers, learning paths, salaries, interviews, freelancing, and life as a student.

You have two modes:
1. **Career Expert**: When the conversation is about careers, skills, learning, jobs, interviews, projects, or studies — give deep, specific, personalized advice.
2. **Helpful Friend**: When someone asks a random question (movies, cricket, general knowledge, jokes, life advice, anything) — answer it naturally and warmly. Don't refuse.

## YOUR PERSONALITY
- Warm, encouraging, and direct — never cold or robotic.
- You celebrate students' progress and potential.
- You use emojis sparingly but effectively for structure and warmth.
- You NEVER ask for name, degree, CGPA, or any personal info upfront.
- If context is helpful, you ask ONE natural question at a time only when it genuinely improves your advice.
- You NEVER say "I need your name/CGPA/degree to help you." That's gatekeeping.

## CAREER REASONING (when relevant)
1. **Reason step by step** — explain WHY you recommend things.
2. **Be specific** — name exact courses, platforms, tools, companies.
3. **Adapt to what they share** — even a simple "I want to be an AI engineer" is enough to start.
4. **Detect career signals naturally** — use context without making a big deal of it.

## WHAT YOU NEVER DO
- Never open with "Could you share your name/degree/CGPA..."
- Never give a questionnaire or checklist of things to fill out
- Never block helping someone because they didn't provide info
- Never say "I'm just an AI" as a cop-out
- Never give one-line generic answers when depth is needed
- Never fabricate real-time facts — always flag knowledge cutoff uncertainty
- **CRITICAL**: Never guess about current government, elections, leaders, or breaking news{rag_section}
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


def get_ai_response(messages: list[dict], model_hint: str | None = None, db: Session | None = None) -> str:
    """
    Get an AI response using the unified provider (Groq → Gemini → Claude).
    Falls back through providers automatically if one is unavailable.
    
    Integrates RAG context retrieval for knowledge grounding to prevent hallucination.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model_hint: Optional model selection hint
        db: Database session for RAG knowledge retrieval
    
    Returns:
        AI response text (grounded in RAG knowledge)
    """
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break

    # Retrieve RAG context if database is available
    rag_context = ""
    confidence_score = 0.0
    
    if user_query and db:
        try:
            # Load knowledge base from DB (includes all defaults + custom entries)
            rag_service.load_knowledge_base(db)
            
            # Retrieve relevant context with confidence scoring
            context_text, confidence_score = rag_service.retrieve_context_text(
                user_query, 
                top_k=5,  # Retrieve top 5 most relevant documents
                max_chars=3500,
                include_sources=True
            )
            
            if context_text:
                rag_context = context_text
                logger.info(f"Retrieved RAG context ({len(context_text)} chars, confidence={confidence_score:.2f}) "
                           f"for query: '{user_query[:100]}'")
                
                # Log confidence level
                if confidence_score >= 0.7:
                    logger.debug("High confidence in RAG retrieval — prioritize this context")
                elif confidence_score >= 0.4:
                    logger.debug("Moderate confidence in RAG retrieval")
                else:
                    logger.debug("Low confidence in RAG retrieval — AI should acknowledge uncertainty")
            else:
                logger.info(f"No RAG context found for query: '{user_query[:100]}'")
                
        except Exception as e:
            logger.warning(f"RAG retrieval failed, continuing without context: {e}")
            rag_context = ""
            confidence_score = 0.0
    else:
        if not user_query:
            logger.debug("Empty user query, skipping RAG retrieval")
        else:
            logger.debug("No database session available for RAG retrieval")

    system_prompt = _build_system_prompt(rag_context)
    
    try:
        response = chat_complete(
            messages=messages,
            system_prompt=system_prompt,
            model_hint=model_hint,
            temperature=0.4,
            max_tokens=2000,
        )
        logger.info(f"AI response generated ({len(response)} chars) "
                   f"with RAG confidence={confidence_score:.2f}")
        return response
    except RuntimeError as e:
        logger.error(f"AI service unavailable: {e}")
        return (
            f"⚠️ AI service unavailable: {e}\n\n"
            "Please set at least one of GROQ_API_KEY, GEMINI_API_KEY, or ANTHROPIC_API_KEY "
            "in your backend .env file."
        )
