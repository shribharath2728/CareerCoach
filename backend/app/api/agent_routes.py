"""
Agent API Routes — /agent/*
Exposes the reasoning pipeline endpoints.
"""
import io
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.reasoning_agent import (
    run_full_agent_analysis,
    simulate_career_growth,
    analyze_resume_text,
    calculate_job_readiness,
    get_project_mentor_recommendations,
    generate_agent_chat_response,
    CAREER_SKILL_MAP,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────────────────────────────

class ProfilePayload(BaseModel):
    name: Optional[str] = ""
    degree: Optional[str] = ""
    branch: Optional[str] = ""
    year: Optional[str] = ""
    cgpa: Optional[str] = ""
    skills: Optional[List[str]] = []
    certifications: Optional[List[str]] = []
    projects: Optional[List[str]] = []
    interests: Optional[List[str]] = []
    career_goal: str
    model: Optional[str] = None


class SimulationPayload(BaseModel):
    profile: dict
    career_goal: str
    hours_per_day: float = 2.0
    months: int = 6
    model: Optional[str] = None


class ResumeAnalyzePayload(BaseModel):
    resume_text: str
    career_goal: str
    model: Optional[str] = None


class JobReadinessPayload(BaseModel):
    profile: dict
    career_goal: str
    model: Optional[str] = None


class ProjectMentorPayload(BaseModel):
    profile: dict
    career_goal: str
    available_hours_per_week: int = 10
    model: Optional[str] = None


class AgentChatPayload(BaseModel):
    messages: List[dict]
    user_profile: Optional[dict] = {}
    model: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/analyze")
def full_analysis(payload: ProfilePayload):
    """Run the full 7-step reasoning pipeline for a user profile."""
    try:
        profile = payload.dict(exclude={"career_goal", "model"})
        result = run_full_agent_analysis(profile, payload.career_goal, payload.model)
        return result
    except Exception as e:
        logger.exception("Agent analysis failed")
        raise HTTPException(status_code=500, detail=f"Agent analysis error: {e!s}")


@router.post("/simulate")
def career_simulation(payload: SimulationPayload):
    """Career Simulation Engine — predict trajectory based on study hours."""
    try:
        result = simulate_career_growth(
            payload.profile,
            payload.career_goal,
            payload.hours_per_day,
            payload.months,
            payload.model,
        )
        return result
    except Exception as e:
        logger.exception("Simulation failed")
        raise HTTPException(status_code=500, detail=f"Simulation error: {e!s}")


@router.post("/resume-analyze")
def analyze_resume(payload: ResumeAnalyzePayload):
    """Analyze resume text — ATS score, keywords, improvements."""
    if not payload.resume_text.strip():
        raise HTTPException(status_code=400, detail="Resume text is required")
    try:
        result = analyze_resume_text(payload.resume_text, payload.career_goal, payload.model)
        return result
    except Exception as e:
        logger.exception("Resume analysis failed")
        raise HTTPException(status_code=500, detail=f"Resume analysis error: {e!s}")


@router.post("/resume-upload")
async def upload_resume(
    file: UploadFile = File(...),
    career_goal: str = Form(...),
    model: Optional[str] = Form(None),
):
    """Upload a PDF resume and analyze it."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    try:
        contents = await file.read()
        # Try pdfplumber first, fall back to pypdf
        resume_text = ""
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                resume_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        except ImportError:
            try:
                from pypdf import PdfReader
                reader = PdfReader(io.BytesIO(contents))
                resume_text = "\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                raise HTTPException(status_code=500, detail="PDF parsing library not installed. Install pdfplumber.")

        if not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. Please upload a text-based PDF.")

        result = analyze_resume_text(resume_text, career_goal, model)
        result["extracted_text_preview"] = resume_text[:500]
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Resume upload/analysis failed")
        raise HTTPException(status_code=500, detail=f"Resume processing error: {e!s}")


@router.post("/job-readiness")
def job_readiness(payload: JobReadinessPayload):
    """Calculate multi-dimensional job readiness score."""
    try:
        result = calculate_job_readiness(payload.profile, payload.career_goal, payload.model)
        return result
    except Exception as e:
        logger.exception("Job readiness calculation failed")
        raise HTTPException(status_code=500, detail=f"Job readiness error: {e!s}")


@router.post("/project-mentor")
def project_mentor(payload: ProjectMentorPayload):
    """Get project recommendations based on skill level and goal."""
    try:
        result = get_project_mentor_recommendations(
            payload.profile,
            payload.career_goal,
            payload.available_hours_per_week,
            payload.model,
        )
        return result
    except Exception as e:
        logger.exception("Project mentor failed")
        raise HTTPException(status_code=500, detail=f"Project mentor error: {e!s}")


@router.post("/chat")
def agent_chat(payload: AgentChatPayload):
    """Intelligent agent chat that follows the reasoning workflow."""
    try:
        result = generate_agent_chat_response(
            payload.messages,
            payload.user_profile or {},
            payload.model,
        )
        return result
    except Exception as e:
        logger.exception("Agent chat failed")
        raise HTTPException(status_code=500, detail=f"Agent chat error: {e!s}")


@router.get("/careers")
def list_careers():
    """List available career paths in the knowledge base."""
    return {
        "careers": [
            {"name": name, "required_count": len(data.get("required_skills", [])), "salary": data.get("salary_range", {})}
            for name, data in CAREER_SKILL_MAP.items()
        ]
    }
