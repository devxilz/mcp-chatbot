import chromadb
from app.utils.model_loder import get_model
from functools import lru_cache

@lru_cache
def get_chroma_client():
    return chromadb.Client()

@lru_cache
def get_memory_collection():
    client = get_chroma_client()
    try:
        return client.get_collection(name="memories")
    except:
        return client.create_collection(
            name="memories",
            metadata={"hnsw:space": "cosine"}
        )

@lru_cache
def get_embedding_model():
    return get_model()
