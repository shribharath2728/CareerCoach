from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.resume import Resume
from app.models.user import User
from app.schemas.resume import ResumeUpsert, ResumeResponse, JDAnalyzeRequest
from app.services import groq_services

router = APIRouter()

@router.get("/user/{user_id}", response_model=ResumeResponse)
def get_user_resume(user_id: int, db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.updated_at.desc()).first()
    if not r:
        raise HTTPException(status_code=404, detail="No resume found")
    return r

@router.put("/", response_model=ResumeResponse)
def upsert_resume(payload: ResumeUpsert, db: Session = Depends(get_db)):
    existing = db.query(Resume).filter(Resume.user_id == payload.user_id).first()
    title = payload.title or "My Resume"
    if existing:
        existing.content = payload.content
        existing.title = title
        db.commit()
        db.refresh(existing)
        return existing
    r = Resume(user_id=payload.user_id, title=title, content=payload.content)
    db.add(r)
    db.commit()
    db.refresh(r)
    return r

@router.post("/user/{user_id}/analyze")
def analyze_jd(user_id: int, body: JDAnalyzeRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    resume = db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.updated_at.desc()).first()
    if not resume:
        raise HTTPException(status_code=400, detail="Save a resume first")
    try:
        data = groq_services.analyze_resume_vs_jd(resume.content, body.jd_text, model=user.ai_model)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    sug = data.get("suggestions")
    if isinstance(sug, list):
        data["suggestions"] = "\n".join(str(x) for x in sug)
    elif sug is None:
        data["suggestions"] = ""
    return data
