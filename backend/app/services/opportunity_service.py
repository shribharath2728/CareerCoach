from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.services import groq_services

def get_suggested_opportunities(db: Session, user_id: int) -> List[Dict[str, Any]]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.field_of_study:
        # Default suggestions for general profiles
        return groq_services.suggest_career_opportunities("General/Undecided")
    
    return groq_services.suggest_career_opportunities(
        field_of_study=user.field_of_study,
        education_level=user.education_level,
        model=user.ai_model
    )
