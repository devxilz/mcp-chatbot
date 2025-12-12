# app/core/re_rank.py

import time
import math
import logging

logger = logging.getLogger(__name__)

def cosine_to_similarity(distance):# convert cosine distance to similarity (0 to 1)
    return max(0.0, min(1.0, 1 - distance))


# ---------------------------------------------------------
# 2. Recency score with robust error handling
# ---------------------------------------------------------

def recency_score(timestamp, half_life_hours=720):
    """
    Compute recency using exponential decay.
    More robust:
    - returns 0.0 on invalid timestamps
    - clamps future timestamps mildly (0.9)
    - no silent failures
    """

    now = time.time()

    if timestamp is None:
        return 0.0

    try:
        ts = float(timestamp)
    except (TypeError, ValueError):
        logger.warning(f"Invalid timestamp in memory: {timestamp}")
        return 0.0

    if ts > now + 5:  # Very future timestamps (misconfigured clock)
        logger.warning(f"Future timestamp detected: {timestamp}")
        return 0.5

    if ts > now:  # Slightly future timestamps are okay
        return 0.9

    age_hours = max(0.0, (now - ts) / 3600)
    score = 0.5 ** (age_hours / half_life_hours)
    return max(0.0, min(1.0, score))


# ---------------------------------------------------------
# 3. Memory type weights
# ---------------------------------------------------------

MEMORY_TYPE_WEIGHTS = {
    "personal_info": 0.95,
    "goal": 0.90,
    "task": 0.88,
    "preference": 0.75,
    "fact": 0.55,
    "short_term": 0.50,
    "compressed": 0.45,
}


# ---------------------------------------------------------
# 4. Main re-ranking function
# ---------------------------------------------------------

def re_rank(memories):
    """
    Rank memories using stable scoring:
    - semantic similarity
    - recency
    - LLM-assigned importance
    - memory type weight
    """

    if not isinstance(memories, list):
        logger.error("re_rank(): expected list, received:", type(memories))
        return []

    ranked = []
    seen_ids = set()  # prevent duplicates

    for mem in memories:
        if not isinstance(mem, dict):
            logger.warning(f"Invalid memory format skipped: {mem}")
            continue

        mem_id = mem.get("id")
        if mem_id in seen_ids:
            continue
        seen_ids.add(mem_id)

        meta = mem.get("metadata", {}) or {}

        # Extract metadata with full validation
        mem_type = meta.get("memory_type", "fact")
        type_score = MEMORY_TYPE_WEIGHTS.get(mem_type, 0.50)

        # Importance
        importance_raw = meta.get("importance", 0.4)
        try:
            importance = float(importance_raw)
            importance = max(0.0, min(1.0, importance))
        except Exception:
            logger.warning(f"Invalid importance value: {importance_raw}")
            importance = 0.4

        created_at = meta.get("created_at")

        # Calculate component scores
        semantic = cosine_to_similarity(mem.get("distance"))
        recent = recency_score(created_at)

        # Weighted score composition
        final_score = (
            semantic * 0.50 +
            recent * 0.20 +
            importance * 0.20 +
            type_score * 0.10
        )

        ranked.append({
            **mem,
            "_rank_semantic": semantic,
            "_rank_recency": recent,
            "_rank_importance": importance,
            "_rank_type": type_score,
            "final_score": final_score,
        })

    # Sort by final score
    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked