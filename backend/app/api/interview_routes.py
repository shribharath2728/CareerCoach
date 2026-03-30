from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.interview import (
    InterviewStartRequest,
    InterviewSessionResponse,
    GenerateQuestionRequest,
    InterviewQuestionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services import interview_service

router = APIRouter()

@router.get("/user/{user_id}/history")
def get_interview_history(user_id: int, db: Session = Depends(get_db)):
    rows = interview_service.get_user_interview_history(user_id, db)
    return [
        {
            "id": r.id,
            "role": r.role,
            "difficulty": r.difficulty,
            "interview_type": r.interview_type,
            "created_at": r.session_date,
        }
        for r in rows
    ]

@router.get("/user/{user_id}/analytics")
def get_analytics(user_id: int, db: Session = Depends(get_db)):
    return interview_service.user_analytics(user_id, db)

@router.post("/start", response_model=InterviewSessionResponse)
def start_interview(body: InterviewStartRequest, db: Session = Depends(get_db)):
    try:
        s = interview_service.start_session(
            db,
            body.user_id,
            body.role,
            body.interview_type,
            body.difficulty,
        )
        return s
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-question", response_model=InterviewQuestionResponse)
def generate_question(body: GenerateQuestionRequest, db: Session = Depends(get_db)):
    try:
        q = interview_service.generate_question_for_session(db, body.session_id)
        pts = q.expected_answer_points if isinstance(q.expected_answer_points, list) else []
        return InterviewQuestionResponse(
            id=q.id,
            session_id=q.session_id,
            question_text=q.question_text,
            expected_answer_points=pts,
            category=q.category,
            difficulty=q.difficulty,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer(body: SubmitAnswerRequest, db: Session = Depends(get_db)):
    try:
        ev = interview_service.submit_answer_for_question(db, body.question_id, body.answer_text)
        return SubmitAnswerResponse(evaluation=ev)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
