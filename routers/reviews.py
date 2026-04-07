from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import get_current_user
from models.user import UserDB
from models.review import ReviewCreate, ReviewResponse, ReviewDB

router = APIRouter(prefix="/companies/{company_id}/reviews", tags=["reviews"])

@router.get("/", response_model=list[ReviewResponse])
def get_reviews(company_id: int, db: Session = Depends(get_db)):
    return db.query(ReviewDB).filter(ReviewDB.company_id == company_id).all()

@router.post("/", response_model=ReviewResponse)
def create_review(company_id: int, review: ReviewCreate, db: Session = Depends(get_db), current_user: UserDB = Depends(get_current_user)):
    db_review = ReviewDB(company_id=company_id, rating=review.rating, comment=review.comment)
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    return db_review
