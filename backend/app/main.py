import os
import json
from fastapi import FastAPI, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.database import init_db, get_session, SessionLocal, Conversation
from app.models import ChatRequest, ChatResponse, IngestRequest
from app.rag.retriever import retrieve
import httpx
from app.rag.generator import generate_answer, generate_stream
from app.rag.embedder import get_embeddings
from app.rag.confidence import evaluate_confidence
from app.ingest.pipeline import ingest_all
from app.review.router import router as review_router
from app.portal.router import router as portal_router
from app.config import OLLAMA_BASE_URL, LLM_MODEL

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _warmup_llm():
    with httpx.Client() as client:
        client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={"model": LLM_MODEL, "messages": [{"role": "user", "content": "Hi"}], "stream": False, "options": {"num_predict": 1}},
            timeout=120,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    get_embeddings()
    _warmup_llm()
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
app.include_router(portal_router)


_FALLBACK_ANSWER = "请稍等，我们正在查询，建议您拨打客服热线 400-888-8888 或联系在线客服咨询更多详情。"
_UNWANTED_PATTERNS = [
    "暂无相关信息", "没有相关信息", "没有找到", "无法为您解答",
    "不太清楚", "暂时没有", "我这边没有", "没有关于",
    "建议您直接访问官网", "建议您访问", "去官网查看", "网站查看",
    "建议您直接联系", "暂未提供",
]


def _sanitize_answer(answer: str) -> str:
    for pattern in _UNWANTED_PATTERNS:
        if pattern in answer:
            return _FALLBACK_ANSWER + "\n\n[自信度: 1]"
    return answer


def _sse(event: str, data: object) -> str:
    return f"data: {json.dumps({'type': event, **data}, ensure_ascii=False)}\n\n"


@app.post("/api/chat/stream")
def chat_stream(body: ChatRequest):
    contexts, scores = retrieve(body.question)

    def generate():
        if not contexts:
            db = SessionLocal()
            try:
                conv = Conversation(
                    session_id=body.session_id, question=body.question,
                    answer=_FALLBACK_ANSWER, confidence=0.0, need_review=True,
                )
                db.add(conv)
                db.commit()
                conv_id = conv.id
            finally:
                db.close()
            yield _sse("token", {"content": _FALLBACK_ANSWER})
            yield _sse("meta", {"confidence": 0.0, "need_review": True, "conversation_id": conv_id})
            return

        full_answer = ""
        try:
            for token in generate_stream(body.question, contexts):
                full_answer += token
                yield _sse("token", {"content": token})
        except Exception as e:
            err_msg = f"系统处理出错，请稍后重试。"
            yield _sse("token", {"content": err_msg})
            full_answer = err_msg

        full_answer = _sanitize_answer(full_answer) if full_answer else _FALLBACK_ANSWER
        confidence, need_review = evaluate_confidence(scores, full_answer) if full_answer else (0.0, True)

        db = SessionLocal()
        try:
            conv = Conversation(
                session_id=body.session_id, question=body.question,
                answer=full_answer, confidence=confidence, need_review=need_review,
            )
            db.add(conv)
            db.commit()
            conv_id = conv.id
        finally:
            db.close()

        yield _sse("meta", {"confidence": confidence, "need_review": need_review, "conversation_id": conv_id})

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_session)):
    contexts, scores = retrieve(body.question)

    if not contexts:
        conv = Conversation(
            session_id=body.session_id,
            question=body.question,
            answer=_FALLBACK_ANSWER,
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
    answer = _sanitize_answer(answer)
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
def ingest(body: IngestRequest, db: Session = Depends(get_session)):
    results = ingest_all(db)
    return {"results": results}


@app.get("/api/health")
def health():
    return {"status": "ok"}
