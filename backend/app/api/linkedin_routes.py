from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.linkedin import LinkedInProfile
from app.schemas.linkedin import LinkedInProfileCreate, LinkedInProfileResponse

router = APIRouter()

def _dump(data: LinkedInProfileCreate) -> dict:
    return data.model_dump() if hasattr(data, "model_dump") else data.dict()

@router.get("/user/{user_id}", response_model=LinkedInProfileResponse)
def get_linkedin_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user_id).first()
    if not profile:
        # Return a dummy profile with default values instead of 404
        # to allow the frontend to handle the "missing profile" state gracefully.
        return LinkedInProfile(id=0, user_id=user_id, profile_url="", summary="", experience="", education="", skills="")
    return profile

@router.post("/user/{user_id}", response_model=LinkedInProfileResponse)
def create_linkedin_profile(user_id: int, profile: LinkedInProfileCreate, db: Session = Depends(get_db)):
    db_profile = LinkedInProfile(**_dump(profile), user_id=user_id)
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.put("/user/{user_id}", response_model=LinkedInProfileResponse)
def update_linkedin_profile(user_id: int, profile: LinkedInProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user_id).first()
    if not db_profile:
        # Create LinkedIn profile if it doesn't exist (Upsert logic)
        db_profile = LinkedInProfile(**_dump(profile), user_id=user_id)
        db.add(db_profile)
    else:
        # Update existing profile
        for key, value in _dump(profile).items():
            setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile

@router.delete("/user/{user_id}")
def delete_linkedin_profile(user_id: int, db: Session = Depends(get_db)):
    db_profile = db.query(LinkedInProfile).filter(LinkedInProfile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="LinkedIn profile not found")
    db.delete(db_profile)
    db.commit()
    return {"message": "LinkedIn profile deleted"}
