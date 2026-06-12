from langchain_ollama import OllamaEmbeddings
from app.config import OLLAMA_BASE_URL, EMBED_MODEL

_embeddings = None


def get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = OllamaEmbeddings(
            model=EMBED_MODEL,
            base_url=OLLAMA_BASE_URL,
        )
    return _embeddings
