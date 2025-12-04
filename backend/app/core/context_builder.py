import numpy as np

def cosine_similarity(a, b):
    return float(np.dot(a, b))

class ContextBuilder:
    def __init__(self, max_tokens=3000, recent_limit=10, dedupe_threshold=0.88):
        self.max_tokens = max_tokens
        self.recent_limit = recent_limit
        self.dedupe_threshold = dedupe_threshold

    # Build context from various sources
    def build(self, query, session_messages, memories, user_profile=None):
        context = []

        # 1. Add profile
        if user_profile:
            context.append({
                "source": "profile",
                "text": user_profile,
                "metadata": {"memory_type": "profile", "importance": 1.0}
            })

        # 2. Add long-term memories
        for mem in memories:
            context.append({
                "source": "memory",
                "text": mem["text"],
                "metadata": mem["metadata"],
                "distance": mem["distance"],
                "vector": mem.get("vector")
            })

        # 3. Add recent session messages
        recent = session_messages[-self.recent_limit:]
        for msg in recent:
            context.append({
                "source": msg["role"],
                "text": msg["text"],
                "metadata": {"memory_type": "session"}
            })

        # 4. DEDUPE
        context = self.dedupe(context)

        # 5. TRIM
        context = self.trim(context)

        return {
            "context_items": context
        }    

    # Dedupe items based on vector similarity
    def dedupe(self, items):
        seen = []
        out = []

        for item in items:
            v = item.get("vector")
            if not v:
                # If we don't have vector, skip semantic dedupe
                out.append(item)
                continue

            duplicate = False
            for s in seen:
                if cosine_similarity(np.array(v), np.array(s)) >= self.dedupe_threshold:
                    duplicate = True
                    break
            
            if not duplicate:
                out.append(item)
                seen.append(v)           
        return out
    
    # Trim items to fit within max token limit
    def trim(self, items):
        total_chars = 0
        out = []
        limit_chars = self.max_tokens * 4  # approx conversion

        for item in items:
            total_chars += len(item["text"])
            if total_chars > limit_chars:
                break
            out.append(item)
        return out    
