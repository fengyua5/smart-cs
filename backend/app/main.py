import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import init_db, get_session, Conversation
from app.models import ChatRequest, ChatResponse, IngestRequest
from app.rag.retriever import retrieve
from app.rag.generator import generate_answer
from app.rag.confidence import evaluate_confidence
from app.ingest.pipeline import ingest_all
from app.review.router import router as review_router

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Smart CS - AI 智能客服", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(BASE_DIR, "..", "frontend")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(review_router)


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_session)):
    contexts, scores = retrieve(body.question)

    if not contexts:
        conv = Conversation(
            session_id=body.session_id,
            question=body.question,
            answer="请稍等，我们正在查询，建议您拨打客服热线 400-888-8888 或联系在线客服咨询更多详情。",
            confidence=0.0,
            need_review=True,
        )
        db.add(conv)
        db.commit()
        return ChatResponse(
            answer=conv.answer,
            confidence=0.0,
            need_review=True,
            conversation_id=conv.id,
        )

    answer = generate_answer(body.question, contexts)
    confidence, need_review = evaluate_confidence(scores, answer)

    conv = Conversation(
        session_id=body.session_id,
        question=body.question,
        answer=answer,
        confidence=confidence,
        need_review=need_review,
    )
    db.add(conv)
    db.commit()

    return ChatResponse(
        answer=answer,
        confidence=confidence,
        need_review=need_review,
        conversation_id=conv.id,
    )


@app.post("/api/ingest")
def ingest(body: IngestRequest):
    count = ingest_all()
    return {"message": f"成功导入 {count} 个文档片段"}


@app.get("/api/health")
def health():
    return {"status": "ok"}
