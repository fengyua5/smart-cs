from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_session
from app.review.service import get_pending_reviews, get_review_history, submit_review
from app.models import ReviewItem, ReviewSubmit
from typing import List

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/pending", response_model=List[ReviewItem])
def list_pending(db: Session = Depends(get_session)):
    items = get_pending_reviews(db)
    return [
        ReviewItem(
            id=item.id,
            question=item.question,
            ai_answer=item.answer or "",
            confidence=item.confidence or 0.0,
            created_at=item.created_at.isoformat() if item.created_at else "",
        )
        for item in items
    ]


@router.get("/history", response_model=List[ReviewItem])
def list_history(db: Session = Depends(get_session)):
    items = get_review_history(db)
    return [
        ReviewItem(
            id=item.id,
            question=item.question,
            ai_answer=item.human_answer or item.answer or "",
            confidence=item.confidence or 0.0,
            created_at=item.created_at.isoformat() if item.created_at else "",
        )
        for item in items
    ]


@router.post("/submit")
def submit(body: ReviewSubmit, db: Session = Depends(get_session)):
    conv = submit_review(db, body.conversation_id, body.human_answer, body.approved)
    if conv is None:
        return {"error": "未找到该对话"}
    return {"message": "审核提交成功", "conversation_id": conv.id}
