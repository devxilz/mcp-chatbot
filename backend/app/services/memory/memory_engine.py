import time
import uuid
from typing import List, Dict, Any, Optional

from app.core.service_loader import get_embedding_model, get_memory_collection


class MemoryEngine:
    """
    Robust memory storage layer over ChromaDB.
    Improvements:
    - Strong unique IDs
    - Reliable recall() with .get()
    - Strict metadata normalization
    - Created/updated timestamps
    - Safer search result parsing
    - Guaranteed return structure
    """

    def __init__(self) -> None:
        self.model = get_embedding_model()
        self.collection = get_memory_collection()

    # ---------------------------------------------------------
    # Embedding helper
    # ---------------------------------------------------------
    def embed(self, text: str) -> List[float]:
        vec = self.model.encode(text, convert_to_tensor=False)
        return vec.tolist() if hasattr(vec, "tolist") else vec

    # ---------------------------------------------------------
    # Generate unique memory ID (no collisions)
    # ---------------------------------------------------------
    def _generate_id(self) -> str:
        return str(uuid.uuid4())

    # ---------------------------------------------------------
    # Add memory
    # ---------------------------------------------------------
    def add_memory(
        self,
        user_id: str,
        session_id: str,
        text: str,
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:

        mem_id = self._generate_id()
        timestamp = time.time()

        base_meta: Dict[str, Any] = {
            "user_id": user_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "importance": 0.4,     # default importance
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        if metadata:
            base_meta.update(metadata) # using if because update gives error if metadata is None

        embedding = self.embed(text)

        self.collection.add(
            ids=[mem_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[base_meta],
        )

        return mem_id

    # ---------------------------------------------------------
    # Semantic search
    # ---------------------------------------------------------
    def search_memory(
        self,
        user_id: str,
        query: str,
        k: int = 10,
    ) -> List[Dict[str, Any]]:

        qvec = self.embed(query)

        results = self.collection.query(
            query_embeddings=[qvec],
            n_results=k,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        ids = (results.get("ids") or [[]])[0]
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]

        output = []
        for mid, doc, meta, dist in zip(ids, docs, metas, dists): #zip iterates over multiple lists in parallel
            output.append({
                "id": mid,
                "text": doc,
                "metadata": meta or {},
                "distance": float(dist),
            })

        return output

    # ---------------------------------------------------------
    # Recall all memories for a user (no vector search)
    # ---------------------------------------------------------
    def recall(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Uses .get() instead of .query() = correct & reliable.
        """

        results = self.collection.get(
            where={"user_id": user_id},
            limit=limit,
            include=["documents", "metadatas"],
        )

        ids = results.get("ids") or []
        docs = results.get("documents") or []
        metas = results.get("metadatas") or []

        output = []
        for mid, doc, meta in zip(ids, docs, metas):
            output.append({
                "id": mid,
                "text": doc,
                "metadata": meta or {},
            })

        return output

    # ---------------------------------------------------------
    # Update memory (text or metadata)
    # ---------------------------------------------------------
    def update_memory(
        self,
        memory_id: str,
        new_text: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:

        existing = self.collection.get(ids=[memory_id])
        if not existing.get("ids"):
            return

        old_doc = existing["documents"][0]
        old_meta = existing["metadatas"][0] or {}

        updated_doc = new_text if new_text is not None else old_doc

        updated_meta = dict(old_meta)
        if new_metadata:
            updated_meta.update(new_metadata)

        # preserve created_at
        if "created_at" not in updated_meta:
            updated_meta["created_at"] = old_meta.get("created_at", time.time())

        updated_meta["updated_at"] = time.time()  # new field

        self.collection.update(
            ids=[memory_id],
            documents=[updated_doc],
            metadatas=[updated_meta],
        )

    # ---------------------------------------------------------
    # Delete memory
    # ---------------------------------------------------------
    def delete_memory(self, memory_id: str) -> None:
        self.collection.delete(ids=[memory_id])
