from typing import List, Tuple
from langchain_chroma import Chroma
from app.config import CHROMA_PERSIST_DIR, RETRIEVAL_K
from app.rag.embedder import get_embeddings


def get_vector_store(collection_name: str = "knowledge"):
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        persist_directory=CHROMA_PERSIST_DIR,
    )


def retrieve(query: str, k: int = RETRIEVAL_K) -> Tuple[List[str], List[float]]:
    vector_store = get_vector_store()
    docs_with_scores = vector_store.similarity_search_with_relevance_scores(query, k=k)
    contents = []
    scores = []
    for doc, score in docs_with_scores:
        contents.append(doc.page_content)
        scores.append(score)
    return contents, scores
