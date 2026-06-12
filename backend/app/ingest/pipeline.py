import os
import hashlib
from datetime import datetime, timezone
from langchain_chroma import Chroma
from langchain.schema import Document
from app.config import KNOWLEDGE_DIR, CHROMA_PERSIST_DIR
from app.rag.embedder import get_embeddings
from app.ingest.loader import split_documents
from app.database import KnowledgeFile


def _file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _rebuild_vector_store():
    from app.ingest.loader import load_documents
    docs = load_documents(KNOWLEDGE_DIR)
    if not docs:
        return
    chunks = split_documents(docs)
    Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="knowledge",
    )


def ingest_file(filepath: str, db_session) -> dict:
    filename = os.path.basename(filepath)
    content_hash = _file_hash(filepath)
    file_size = os.path.getsize(filepath)

    existing = db_session.query(KnowledgeFile).filter_by(filename=filename).first()
    if existing and existing.content_hash == content_hash:
        return {"status": "skipped", "filename": filename, "reason": "内容相同，已跳过"}

    dest = os.path.join(KNOWLEDGE_DIR, filename)
    if os.path.abspath(filepath) != os.path.abspath(dest):
        os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
        import shutil
        shutil.copy2(filepath, dest)
        filepath = dest

    _rebuild_vector_store()

    if existing:
        existing.content_hash = content_hash
        existing.chunk_count = _count_chunks(filepath)
        existing.file_size = file_size
        existing.imported_at = datetime.now(timezone.utc)
    else:
        kf = KnowledgeFile(
            filename=filename, content_hash=content_hash,
            chunk_count=_count_chunks(filepath), file_size=file_size,
        )
        db_session.add(kf)
    db_session.commit()

    return {"status": "imported" if not existing else "updated", "filename": filename}


def _count_chunks(filepath: str) -> int:
    doc = Document(page_content=open(filepath, encoding="utf-8").read(), metadata={"source": os.path.basename(filepath)})
    return len(split_documents([doc]))


def ingest_all(db_session=None):
    results = []
    for fname in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not fname.endswith((".md", ".txt")):
            continue
        filepath = os.path.join(KNOWLEDGE_DIR, fname)
        if not os.path.isfile(filepath):
            continue
        result = ingest_file(filepath, db_session)
        results.append(result)
    return results
