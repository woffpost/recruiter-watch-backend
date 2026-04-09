from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import get_current_user
from models.user import UserDB
from models.company import CompanyDB
from models.review import ReviewDB
import pdfplumber
import anthropic
import os
import io
import re 
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/analyze")
def analyze_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    # Читаем PDF
    contents = file.file.read()
    pdf = pdfplumber.open(io.BytesIO(contents))
    text = "\n".join([page.extract_text() or "" for page in pdf.pages])
    
    if not text.strip():
        return {"error": "Could not extract text from PDF"}
    
    # Отправляем в Claude
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze this resume and provide:
1. Current level (Junior/Middle/Senior)
2. Main skills detected
3. What's missing for the next level (3-5 specific points)
4. Recommended job titles to search for

Resume:
{text}

Respond in JSON format:
{{
    "level": "...",
    "skills": [...],
    "gaps": [...],
    "recommended_titles": [...]
}}"""
        }]
    )
    
    import json
    response_text = message.content[0].text
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        result = {"raw": response_text}

    return result




@router.post("/analyze-and-match")
def analyze_and_match(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(get_current_user)
):
    contents = file.file.read()
    pdf = pdfplumber.open(io.BytesIO(contents))
    text = "\n".join([page.extract_text() or "" for page in pdf.pages])

    if not text.strip():
        return {"error": "Could not extract text from PDF"}

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""Analyze this resume and respond ONLY with JSON, no other text:
{{
    "level": "Junior/Middle/Senior",
    "skills": ["skill1", "skill2"],
    "gaps": ["gap1", "gap2"],
    "recommended_titles": ["title1", "title2"]
}}

Resume:
{text}"""
        }]
    )

    import json, re
    response_text = message.content[0].text
    clean = re.sub(r'```json\s*|\s*```', '', response_text).strip()
    try:
        analysis = json.loads(clean)
    except:
        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
        analysis = json.loads(json_match.group()) if json_match else {"raw": response_text}

    skills_query = ",".join(analysis.get("skills", [])[:5])
    companies = db.query(CompanyDB).all()
    
    matched = []
    for company in companies:
        reviews = db.query(ReviewDB).filter(ReviewDB.company_id == company.id).all()
        avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0
        
        score = 0
        if company.tech_stack:
            company_stack = company.tech_stack.lower()
            score = sum(1 for skill in analysis.get("skills", []) if skill.lower() in company_stack)
        
        if score > 0 or avg_rating > 0:
            matched.append({
                "id": company.id,
                "name": company.name,
                "industry": company.industry,
                "tech_stack": company.tech_stack,
                "avg_rating": avg_rating,
                "review_count": len(reviews),
                "skill_match": score
            })

    matched.sort(key=lambda x: (x["skill_match"], x["avg_rating"]), reverse=True)

    return {
        "analysis": analysis,
        "matched_companies": matched[:5]
    }