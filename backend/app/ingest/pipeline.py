import os
from langchain_chroma import Chroma
from app.config import KNOWLEDGE_DIR, CHROMA_PERSIST_DIR
from app.rag.embedder import get_embeddings
from app.ingest.loader import load_documents, split_documents


def ingest_all():
    docs = load_documents(KNOWLEDGE_DIR)
    if not docs:
        print(f"在 {KNOWLEDGE_DIR} 中未找到文档")
        return 0

    chunks = split_documents(docs)
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
        collection_name="knowledge",
    )
    vector_store.persist()
    print(f"成功导入 {len(docs)} 个文档，切分为 {len(chunks)} 个片段")
    return len(chunks)
