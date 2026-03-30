from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserCreate, UserLogin, UserResponse, UserUpdateSettings
from app.services.user_service import (
    create_user_service,
    login_user_service,
    update_user_settings_service,
    get_user_by_id,
)

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    return create_user_service(db, payload)

@router.post("/users/login", response_model=UserResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    return login_user_service(db, payload.email, payload.password)

@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = get_user_by_id(db, user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return u

@router.put("/users/{user_id}/settings", response_model=UserResponse)
def update_settings(user_id: int, payload: UserUpdateSettings, db: Session = Depends(get_db)):
    return update_user_settings_service(db, user_id, payload)
