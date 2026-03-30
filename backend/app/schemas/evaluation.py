from pydantic import BaseModel
from typing import List, Optional

class InterviewEvaluationPayload(BaseModel):
    overall_score: int = 0
    feedback_summary: str = ""
    strengths: List[str] = []
    improvements: List[str] = []
    missed_points: List[str] = []
    hiring_signal: str = "weak"
    difficulty_recommendation: str = "same"
    problem_solving_score: int = 0
    technical_score: int = 0
    communication_score: int = 0
    structure_score: int = 0
    completeness_score: int = 0
    confidence_score: int = 0
    follow_up_question: Optional[str] = None
