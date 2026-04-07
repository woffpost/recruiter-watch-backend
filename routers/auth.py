from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.user import UserCreate, UserResponse, UserDB
from database import get_db
from jose import jwt
from datetime import datetime, timedelta
import bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"

@router.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt())
    db_user = UserDB(email=user.email, hashed_password=hashed.decode("utf-8"))
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/login")
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserDB).filter(UserDB.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(user.password.encode("utf-8"), db_user.hashed_password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode(
        {"sub": db_user.email, "exp": datetime.utcnow() + timedelta(hours=24)},
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return {"access_token": token, "token_type": "bearer"}