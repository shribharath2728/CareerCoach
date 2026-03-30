import json
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.models.user import User
from app.services import groq_services

def get_user_interview_history(user_id: int, db: Session):
    return (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.session_date.desc())
        .all()
    )

def start_session(db: Session, user_id: int, role: str, interview_type: str, difficulty: str) -> InterviewSession:
    s = InterviewSession(
        user_id=user_id,
        role=role,
        interview_type=interview_type,
        difficulty=difficulty,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

def generate_question_for_session(db: Session, session_id: int) -> InterviewQuestion:
    session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    if not session:
        raise ValueError("Session not found")
    user = db.query(User).filter(User.id == session.user_id).first()
    model = user.ai_model if user else None
    
    # Get previous questions to avoid repetition
    prev_qs = db.query(InterviewQuestion.question_text).filter(InterviewQuestion.session_id == session_id).all()
    previous_texts = [q[0] for q in prev_qs]

    data = groq_services.generate_interview_question(
        role=session.role or "Software Engineer",
        interview_type=session.interview_type or "technical",
        difficulty=session.difficulty or "medium",
        model=model,
        previous_questions=previous_texts,
    )

    q = InterviewQuestion(
        session_id=session_id,
        question_text=data["question_text"],
        expected_answer_points=data.get("expected_answer_points") or [],
        category=data.get("category"),
        difficulty=data.get("difficulty"),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q

def submit_answer_for_question(db: Session, question_id: int, answer_text: str) -> dict:
    q = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
    if not q:
        raise ValueError("Question not found")
    session = db.query(InterviewSession).filter(InterviewSession.id == q.session_id).first()
    user = db.query(User).filter(User.id == session.user_id).first() if session else None
    model = user.ai_model if user else None

    expected = q.expected_answer_points if isinstance(q.expected_answer_points, list) else []

    evaluation = groq_services.evaluate_interview_answer(
        role=session.role if session else "",
        question=q.question_text,
        answer=answer_text,
        expected_points=expected,
        difficulty=session.difficulty or "medium",
        interview_type=session.interview_type or "technical",
        model=model,
    )

    q.user_answer = answer_text
    q.feedback = json.dumps(evaluation)
    q.score = int(evaluation.get("overall_score") or 0)

    ans = InterviewAnswer(question_id=question_id, answer_text=answer_text, is_correct=q.score >= 60)
    db.add(ans)
    db.commit()
    db.refresh(q)
    return evaluation

def user_analytics(user_id: int, db: Session) -> dict:
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == user_id).all()
    qs = (
        db.query(func.count(InterviewQuestion.id))
        .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
        .filter(
            InterviewSession.user_id == user_id,
            InterviewQuestion.user_answer.isnot(None),
        )
        .scalar()
    )
    avg_q = (
        db.query(func.avg(InterviewQuestion.score))
        .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
        .filter(
            InterviewSession.user_id == user_id,
            InterviewQuestion.score.isnot(None),
        )
        .scalar()
    )
    avg = round(float(avg_q or 0), 1)
    nq = int(qs or 0)
    si = len(sessions)
    return {
        "sessions": si,
        "avg_score": avg,
        "questions_answered": nq,
        "total_interviews": si,
        "total_questions_answered": nq,
        "average_score": avg,
    }
