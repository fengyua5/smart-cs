from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    session_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    need_review: bool
    conversation_id: int


class ReviewItem(BaseModel):
    id: int
    question: str
    ai_answer: str
    confidence: float
    created_at: str

    class Config:
        from_attributes = True


class ReviewSubmit(BaseModel):
    conversation_id: int
    human_answer: str
    approved: bool


class IngestRequest(BaseModel):
    file_path: Optional[str] = None
    url: Optional[str] = None
    text: Optional[str] = None
