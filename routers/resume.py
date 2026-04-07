from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth_utils import get_current_user
from models.user import UserDB
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