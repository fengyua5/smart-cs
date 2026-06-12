import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5:9b")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3:latest")

CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")
KNOWLEDGE_DIR = os.path.join(BASE_DIR, "knowledge")
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'smart_cs.db')}"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
RETRIEVAL_K = 4
CONFIDENCE_RETRIEVAL_THRESHOLD = 0.65
CONFIDENCE_LLM_THRESHOLD = 6
MAX_HISTORY = 10
