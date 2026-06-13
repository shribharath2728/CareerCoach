from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services import opportunity_service
from typing import List, Dict, Any

router = APIRouter()

@router.get("/{user_id}/discover")
def discover_opportunities(user_id: int, db: Session = Depends(get_db)):
    try:
        return opportunity_service.get_suggested_opportunities(db, user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
