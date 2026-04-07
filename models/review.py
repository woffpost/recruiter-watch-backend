from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base

# ReviewCreate
# company_id: int
# rating: int
# comment: str | None = None

class ReviewCreate(BaseModel):
    rating: int
    comment: str | None = None

class ReviewResponse(BaseModel):
    id: int
    company_id: int
    rating: int
    comment: str | None = None

class ReviewDB(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)