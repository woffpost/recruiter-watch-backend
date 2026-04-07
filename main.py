from fastapi import FastAPI
from routers import companies, reviews, auth, resume

app = FastAPI(title="RecruiterWatch API")
app.include_router(companies.router)
app.include_router(reviews.router)
app.include_router(auth.router)
app.include_router(resume.router)

@app.get("/")

def root():
    return {"message": "RecruiterWatch API is running!"}