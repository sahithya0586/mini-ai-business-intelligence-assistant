from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from analytics import answer_question, ensure_database

app = FastAPI(title="Mini AI Business Intelligence Assistant", version="1.0")

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)

@app.on_event("startup")
def startup():
    ensure_database()

@app.get("/")
def home():
    return {"message": "Sales BI API is running", "docs": "/docs"}

@app.post("/query")
def query(request: QuestionRequest):
    try:
        return answer_question(request.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unable to process question: {str(exc)}")
