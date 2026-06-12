from sqlalchemy.orm import Session
from app.database import Conversation
from datetime import datetime, timezone


def get_pending_reviews(db: Session):
    return (
        db.query(Conversation)
        .filter(Conversation.need_review == True, Conversation.reviewed == False)
        .order_by(Conversation.created_at.desc())
        .all()
    )


def get_review_history(db: Session):
    return (
        db.query(Conversation)
        .filter(Conversation.reviewed == True)
        .order_by(Conversation.created_at.desc())
        .limit(100)
        .all()
    )


def submit_review(db: Session, conversation_id: int, human_answer: str, approved: bool):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        return None
    conv.reviewed = True
    conv.human_answer = human_answer
    if approved:
        conv.answer = human_answer
    db.commit()
    return conv
