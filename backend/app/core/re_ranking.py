# app/core/re_rank.py

import time
import math

def cosine_to_similarity(distance):
    return max(0.0, min(1.0, 1 - distance))


def recency_score(timestamp, half_life_hours=720):
    now = time.time()

    try:
        ts = float(timestamp)
    except (TypeError, ValueError):
        return 0.3

    if ts > now:
        return 0.9

    age_hours = max(0, (now - ts) / 3600)
    score = 0.5 ** (age_hours / half_life_hours)
    return max(0.0, min(1.0, score))


MEMORY_TYPE_WEIGHTS = {
    "personal_info": 0.95,
    "goal": 0.90,
    "task": 0.88,
    "preference": 0.75,
    "fact": 0.55,
    "short_term": 0.50,
    "compressed": 0.45,
}


def re_rank(memories):
    ranked = []

    for mem in memories:
        meta = mem.get("metadata", {})

        mem_type = meta.get("memory_type", "fact")
        importance = float(meta.get("importance", 0.4))
        created_at = meta.get("created_at")

        semantic = cosine_to_similarity(mem.get("distance", 1.0))
        recent = recency_score(created_at)

        type_score = MEMORY_TYPE_WEIGHTS.get(mem_type, 0.50)

        final_score = (
            semantic * 0.50 +
            recent * 0.20 +
            importance * 0.20 +
            type_score * 0.10
        )

        ranked.append({
            **mem,
            "semantic_score": semantic,
            "recency_score": recent,
            "final_score": final_score
        })

    ranked.sort(key=lambda x: x["final_score"], reverse=True)
    return ranked
