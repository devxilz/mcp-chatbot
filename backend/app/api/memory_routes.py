from fastapi import APIRouter, HTTPException, Query
from app.services.memory.memory_engine import MemoryEngine
from app.core.re_ranking import re_rank

router = APIRouter(tags=["Memory Inspection"])

memory_engine = MemoryEngine()

# ------------------------------------------------------
# 1. Get ALL memories for a user (unordered)
# ------------------------------------------------------
@router.get("/memory/{user_id}")
def get_all_memories(user_id: str, limit: int = 100):
    memories = memory_engine.recall(user_id, limit)
    return {"count": len(memories), "memories": memories}


# ------------------------------------------------------
# 2. Search memory & return ranked results
# ------------------------------------------------------
@router.get("/memory/{user_id}/search")
def search_memory(user_id: str, query: str = Query(..., min_length=2), limit: int = 10):
    raw_results = memory_engine.search_memory(user_id, query, k=limit)
    ranked = re_rank(raw_results)
    return {
        "query": query,
        "raw_count": len(raw_results),
        "ranked_count": len(ranked),
        "ranked": ranked
    }


# ------------------------------------------------------
# 3. Delete a memory by ID
# ------------------------------------------------------
@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    try:
        memory_engine.delete_memory(memory_id)
        return {"status": "success", "deleted_id": memory_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
