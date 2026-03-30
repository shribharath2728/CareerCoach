from fastapi import APIRouter
from app.api.user_routes import router as user_router
from app.api.interview_routes import router as interview_router
from app.api.user_chat_routes import router as user_chat_router
from app.api.resume_routes import router as resume_router
from app.api.job_routes import router as job_router
from app.api.linkedin_routes import router as linkedin_router

api_router = APIRouter()

api_router.include_router(user_router, tags=["users"])
api_router.include_router(interview_router, prefix="/interview", tags=["interview"])
api_router.include_router(user_chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(resume_router, prefix="/resumes", tags=["resume"])
api_router.include_router(job_router, prefix="/jobs", tags=["job"])
api_router.include_router(linkedin_router, prefix="/linkedin", tags=["linkedin"])
