import time
from typing import List, Dict, Any, Optional

from app.core.service_loader import get_embedding_model, get_memory_collection
from app.utils.id_utils import generate_memory_id


class MemoryEngine:
    """
    Wrapper around Chroma collection + embedding model.

    Responsibilities:
    - Embed text
    - Add memories with rich metadata (user_id, session_id, type, importance, created_at)
    - Search memories for a user
    - Update / delete / recall memories
    """

    def __init__(self) -> None:
        self.model = get_embedding_model()
        self.collection = get_memory_collection()

    # ---------------------------------------------------------
    # Embedding helper
    # ---------------------------------------------------------
    def embed(self, text: str) -> List[float]:
        vec = self.model.encode(text, convert_to_tensor=False)
        # Some models return numpy arrays; normalize to plain list
        return vec.tolist() if hasattr(vec, "tolist") else vec

    # ---------------------------------------------------------
    # Add a new memory
    # ---------------------------------------------------------
    def add_memory(
        self,
        user_id: str,
        session_id: str,
        text: str,
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Stores a memory in Chroma with consistent metadata:
        - user_id
        - session_id
        - memory_type
        - importance
        - created_at (unix timestamp)
        """

        base_meta: Dict[str, Any] = {
            "user_id": user_id,
            "session_id": session_id,
            "memory_type": memory_type,
            "created_at": time.time(),
        }

        # Merge caller metadata (e.g. importance) on top
        if metadata:
            base_meta.update(metadata)

        # Always ensure importance exists
        if "importance" not in base_meta:
            base_meta["importance"] = 0.4  # neutral default

        mem_id = generate_memory_id(user_id, session_id, text)
        embedding = self.embed(text)

        self.collection.add(
            ids=[mem_id],
            documents=[text],
            metadatas=[base_meta],
            embeddings=[embedding],
        )

        return mem_id

    # ---------------------------------------------------------
    # Semantic search for a user's memories
    # ---------------------------------------------------------
    def search_memory(
        self,
        user_id: str,
        query: str,
        k: int = 10,
    ) -> list[Dict[str, Any]]:
        """
        Returns a list of:
        {
            "id": str,
            "text": str,
            "metadata": dict,
            "distance": float
        }
        """

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

        out: list[Dict[str, Any]] = []
        for mid, doc, meta, dist in zip(ids, docs, metas, dists):
            if meta is None:
                meta = {}
            out.append(
                {
                    "id": mid,
                    "text": doc,
                    "metadata": meta,
                    "distance": float(dist),
                }
            )

        return out

    # ---------------------------------------------------------
    # Get all memories for a user (for debugging / tools)
    # ---------------------------------------------------------
    def recall(self, user_id: str, k: int = 100) -> list[Dict[str, Any]]:
        """
        Recall up to k memories for a user without a specific query.
        Useful for debugging or inspection.
        """

        results = self.collection.query(
            query_texts=["*"],
            n_results=k,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"],
        )

        ids = (results.get("ids") or [[]])[0]
        docs = (results.get("documents") or [[]])[0]
        metas = (results.get("metadatas") or [[]])[0]
        dists = (results.get("distances") or [[]])[0]

        out: list[Dict[str, Any]] = []
        for mid, doc, meta, dist in zip(ids, docs, metas, dists):
            if meta is None:
                meta = {}
            out.append(
                {
                    "id": mid,
                    "text": doc,
                    "metadata": meta,
                    "distance": float(dist),
                }
            )

        return out

    # ---------------------------------------------------------
    # Update an existing memory's text/metadata
    # ---------------------------------------------------------
    def update_memory(
        self,
        memory_id: str,
        new_text: Optional[str] = None,
        new_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Overwrites the document and/or metadata for a memory.
        """

        # Fetch existing to merge metadata
        existing = self.collection.get(ids=[memory_id])

        if not existing.get("ids"):
            return

        old_doc = existing["documents"][0]
        old_meta = existing["metadatas"][0] or {}

        doc = new_text if new_text is not None else old_doc

        meta = dict(old_meta)
        if new_metadata:
            meta.update(new_metadata)

        # Ensure we don't lose required keys
        if "created_at" not in meta:
            meta["created_at"] = time.time()
        if "importance" not in meta:
            meta["importance"] = 0.4

        self.collection.update(
            ids=[memory_id],
            documents=[doc],
            metadatas=[meta],
        )

    # ---------------------------------------------------------
    # Delete a memory by id
    # ---------------------------------------------------------
    def delete_memory(self, memory_id: str) -> None:
        self.collection.delete(ids=[memory_id])
