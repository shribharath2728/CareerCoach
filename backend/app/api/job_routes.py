from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.job import JobApplication
from app.schemas.job import JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse

router = APIRouter()

@router.get("/user/{user_id}", response_model=list[JobApplicationResponse])
def get_user_jobs(user_id: int, db: Session = Depends(get_db)):
    return db.query(JobApplication).filter(JobApplication.user_id == user_id).all()

@router.post("/", response_model=JobApplicationResponse)
def create_job(payload: JobApplicationCreate, db: Session = Depends(get_db)):
    job = JobApplication(
        user_id=payload.user_id,
        company_name=payload.company,
        job_title=payload.role,
        status=payload.status or "Applied",
        notes=payload.notes,
        linkedin_job_url=payload.linkedin_job_url,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.put("/{job_id}", response_model=JobApplicationResponse)
def update_job(job_id: int, payload: JobApplicationUpdate, db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(job, k, v)
    db.commit()
    db.refresh(job)
    return job

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(JobApplication).filter(JobApplication.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"ok": True}
