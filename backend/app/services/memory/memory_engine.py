import time
from app.core.service_loader import get_embedding_model, get_memory_collection
from app.utils.id_utils import generate_memory_id


class MemoryEngine:
    def __init__(self):
        self.model = get_embedding_model()
        self.collection = get_memory_collection()

    # ----------------------------------------
    # Embed text
    # ----------------------------------------
    def embed(self, text: str):
        return self.model.encode(text).tolist()

    # ----------------------------------------
    # Add Memory
    # ----------------------------------------
    def add_memory(self, user_id, session_id, text, 
                   memory_type="short_term", metadata=None):

        memory_id = generate_memory_id(user_id, session_id, text)
        embedding = self.embed(text)

        meta = {
            "user_id": user_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "importance": metadata.get("importance", 0.5) if metadata else 0.5,
            "created_at": int(time.time())
        }

        self.collection.add(
            ids=[memory_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[meta]
        )

        return memory_id

    # ----------------------------------------
    # Search Memory
    # ----------------------------------------
    def search_memory(self, user_id, query, k=10):

        qvec = self.embed(query)

        results = self.collection.query(
            query_embeddings=[qvec],
            n_results=k,
            where={"user_id": user_id}
        )

        docs = results.get("documents", [[]])[0]
        ids = results.get("ids", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        return [
            {
                "id": mid,
                "text": doc,
                "metadata": meta,
                "distance": dist
            }
            for mid, doc, meta, dist in zip(ids, docs, metas, dists)
        ]

    # ----------------------------------------
    # Update Memory
    # ----------------------------------------
    def update_memory(self, memory_id, new_text=None, new_metadata=None):

        updated_docs = [new_text] if new_text else None
        updated_metas = [new_metadata] if new_metadata else None

        self.collection.update(
            ids=[memory_id],
            documents=updated_docs,
            metadatas=updated_metas
        )

        return True

    # ----------------------------------------
    # Delete Memory
    # ----------------------------------------
    def delete_memory(self, memory_id):
        self.collection.delete(ids=[memory_id])
        return True

    # ----------------------------------------
    # Recall All Memories for a User
    # ----------------------------------------
    def recall(self, user_id, k=100):
        return self.collection.query(
            query_texts=[" "],
            n_results=k,
            where={"user_id": user_id}
        )


memory_engine = MemoryEngine()
