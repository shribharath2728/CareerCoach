from pydantic import BaseModel
from typing import Any, Optional, List

class InterviewStartRequest(BaseModel):
    user_id: int
    role: str
    interview_type: str
    difficulty: str
    field_of_study: Optional[str] = None

class InterviewSessionResponse(BaseModel):
    id: int
    user_id: int
    role: Optional[str] = None
    interview_type: Optional[str] = None
    difficulty: Optional[str] = None

    class Config:
        from_attributes = True

class GenerateQuestionRequest(BaseModel):
    session_id: int

class InterviewQuestionResponse(BaseModel):
    id: int
    session_id: int
    question_text: str
    expected_answer_points: Optional[List[str]] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None

    class Config:
        from_attributes = True

class SubmitAnswerRequest(BaseModel):
    question_id: int
    answer_text: str

class SubmitAnswerResponse(BaseModel):
    evaluation: dict[str, Any]
