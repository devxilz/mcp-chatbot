import chromadb
from app.utils.model_loder import get_model
from functools import lru_cache
from app.core.settings import settings
import os

CHROMA_DIR = os.path.join(settings.DATA_DIR, "chroma")
os.makedirs(CHROMA_DIR, exist_ok=True)

@lru_cache
def get_chroma_client():
    """Return a SINGLE persistent Chroma client."""
    return chromadb.PersistentClient(path=CHROMA_DIR)

@lru_cache
def get_memory_collection():
    """Return the 'memories' collection, creating it if needed."""
    client = get_chroma_client()

    try:
        return client.get_collection(name="memories")
    except Exception:
        return client.create_collection(
            name="memories",
            metadata={"hnsw:space": "cosine"}
        )

@lru_cache
def get_embedding_model():
    """Return a SINGLE embedding model instance."""
    return get_model()
