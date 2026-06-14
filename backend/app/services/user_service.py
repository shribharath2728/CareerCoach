import secrets
import hashlib
import base64
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdateSettings

def _hash(pw: str) -> str:
    """
    Simple PBKDF2 hashing that doesn't have bcrypt's 72-byte limitation.
    More secure than plain SHA256 and compatible with all password lengths.
    """
    if not pw:
        pw = secrets.token_hex(8)  # Random password for guests
    
    # Use PBKDF2 with SHA256 (100k iterations is industry standard)
    salt = secrets.token_bytes(32)
    key = hashlib.pbkdf2_hmac('sha256', pw.encode('utf-8'), salt, 100000)
    
    # Return salt + key encoded in base64 for storage
    return base64.b64encode(salt + key).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a PBKDF2 hash."""
    try:
        # Decode the stored hash
        decoded = base64.b64decode(hashed)
        salt = decoded[:32]
        stored_key = decoded[32:]
        
        # Derive key from plain password using the same salt
        key = hashlib.pbkdf2_hmac('sha256', plain.encode('utf-8'), salt, 100000)
        
        # Compare keys (constant-time comparison)
        return secrets.compare_digest(key, stored_key)
    except Exception:
        return False

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()

def create_user_service(db: Session, payload: UserCreate) -> User:
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name or "User",
        hashed_password=_hash(payload.password),
        is_guest=payload.is_guest,
        theme=payload.theme or "dark",
        ai_name="Nova",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def login_user_service(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.is_guest:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Guest accounts cannot log in this way")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return user

def update_user_settings_service(db: Session, user_id: int, payload: UserUpdateSettings) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user

def get_current_user(db: Session, user_id: int) -> User:
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
