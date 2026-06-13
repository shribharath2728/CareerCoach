import json
from datetime import date
from typing import Optional
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

def start_session(db: Session, user_id: int, role: str, interview_type: str, difficulty: str, field_of_study: Optional[str] = None) -> InterviewSession:
    s = InterviewSession(
        user_id=user_id,
        role=role,
        interview_type=interview_type,
        difficulty=difficulty,
        field_of_study=field_of_study,
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
        field_of_study=session.field_of_study or (user.field_of_study if user else None),
        model=model,
        previous_questions=previous_texts,
        coaching_style=user.coaching_style if user else None,
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

def _update_streak(db: Session, user: User):
    """Update user's daily practice streak safely."""
    try:
        today = date.today()
        last = user.last_practice_date
        if last is None or last < today:
            # First practice today — check if yesterday too
            if last is not None:
                from datetime import timedelta
                yesterday = today - timedelta(days=1)
                if last == yesterday:
                    user.streak_count = (user.streak_count or 0) + 1
                else:
                    user.streak_count = 1  # streak broken, reset to 1
            else:
                user.streak_count = 1
            user.last_practice_date = today
            db.commit()
    except Exception:
        pass  # Streak update is non-critical, never crash the main flow

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
        coaching_style=user.coaching_style if user else None,
    )

    q.user_answer = answer_text
    q.feedback = json.dumps(evaluation)
    q.score = int(evaluation.get("overall_score") or 0)

    ans = InterviewAnswer(question_id=question_id, answer_text=answer_text, is_correct=q.score >= 60)
    db.add(ans)
    db.commit()
    db.refresh(q)

    # Update streak (non-critical)
    if user:
        _update_streak(db, user)

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

    # Best score
    best_q = (
        db.query(func.max(InterviewQuestion.score))
        .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
        .filter(InterviewSession.user_id == user_id)
        .scalar()
    )
    best = int(best_q or 0)

    # Dimension averages — parse from feedback JSON stored in question.feedback
    dimension_avgs = _calc_dimension_averages(db, user_id)

    # Streak info
    user = db.query(User).filter(User.id == user_id).first()
    streak = getattr(user, "streak_count", 0) or 0
    last_practice = str(getattr(user, "last_practice_date", None) or "")

    return {
        "sessions": si,
        "avg_score": avg,
        "questions_answered": nq,
        "total_interviews": si,
        "total_questions_answered": nq,
        "average_score": avg,
        "best_score": best,
        "streak_count": streak,
        "last_practice_date": last_practice,
        "dimension_averages": dimension_avgs,
    }

def _calc_dimension_averages(db: Session, user_id: int) -> dict:
    """Parse feedback JSON from answered questions and compute avg per dimension."""
    keys = [
        "technical_score", "problem_solving_score", "communication_score",
        "structure_score", "completeness_score", "confidence_score",
    ]
    totals = {k: 0.0 for k in keys}
    counts = {k: 0 for k in keys}

    try:
        answered = (
            db.query(InterviewQuestion.feedback)
            .join(InterviewSession, InterviewQuestion.session_id == InterviewSession.id)
            .filter(
                InterviewSession.user_id == user_id,
                InterviewQuestion.feedback.isnot(None),
            )
            .all()
        )
        for (fb,) in answered:
            if not fb:
                continue
            try:
                data = json.loads(fb)
            except Exception:
                continue
            for k in keys:
                val = data.get(k)
                if val is not None:
                    try:
                        totals[k] += float(val)
                        counts[k] += 1
                    except (TypeError, ValueError):
                        pass
    except Exception:
        pass  # Non-critical

    return {
        k: round(totals[k] / counts[k], 1) if counts[k] > 0 else 0
        for k in keys
    }
