from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from database import Base

class CompanyCreate(BaseModel):
    name: str
    industry: str
    website: str | None = None
    tech_stack: str | None = None

class CompanyResponse(BaseModel):
    id: int
    name: str
    industry: str
    website: str | None = None
    tech_stack: str | None = None

class CompanyDB(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    industry = Column(String, nullable=False)
    website = Column(String, nullable=True)
    tech_stack = Column(String, nullable=True)