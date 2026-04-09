import anthropic 
import os
from dotenv import load_dotenv
from models.review import ReviewDB
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.company import CompanyCreate, CompanyResponse, CompanyDB
from database import get_db

load_dotenv()
router = APIRouter(prefix="/companies", tags=["companies"])

@router.get("/", response_model=list[CompanyResponse])
def get_companies(db: Session = Depends(get_db)):
    return db.query(CompanyDB).all()

@router.get("/match")
def match_companies(skills: str, db: Session = Depends(get_db)):
    skill_list = [s.strip().lower() for s in skills.split(",")]
    companies = db.query(CompanyDB).all()
    
    results = []
    for company in companies:
        reviews = db.query(ReviewDB).filter(ReviewDB.company_id == company.id).all()
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0
        
        score = 0
        if company.tech_stack:
            company_stack = company.tech_stack.lower()
            matches = sum(1 for skill in skill_list if skill in company_stack)
            score = matches
        
        if score > 0 or avg_rating > 0:
            results.append({
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "tech_stack": company.tech_stack,
                "avg_rating": avg_rating,
                "review_count": len(reviews),
                "skill_match": score
            })
    
    results.sort(key=lambda x: (x["skill_match"], x["avg_rating"]), reverse=True)
    return results[:10]

@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = CompanyDB(**company.model_dump())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company(company_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(company_id: int, company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    for key, value in company.model_dump().items():
        setattr(db_company, key, value)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.delete("/{company_id}")
def delete_company(company_id: int, db: Session = Depends(get_db)):
    db_company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not db_company:
        raise HTTPException(status_code=404, detail="Company not found")
    db.delete(db_company)
    db.commit()
    return {"message": "Company deleted"}

@router.get("/{company_id}/summary")
def get_company_summary(company_id: int, db: Session = Depends(get_db)):
    company = db.query(CompanyDB).filter(CompanyDB.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    reviews = db.query(ReviewDB).filter(ReviewDB.company_id == company_id).all()
    if not reviews:
        return {"summary": "No reviews yet"}
    
    reviews_text = "\n".join([
        f"Rating: {r.rating}/5. Comment: {r.comment or 'No comment'}"
        for r in reviews
    ])
    
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"Based on these employee reviews for {company.name}, write a brief 2-3 sentence summary of the company as an employer:\n\n{reviews_text}"
        }]
    )
    
    return {"summary": message.content[0].text}