import hashlib
import time
import re

def sanitize(text: str) -> str:
    """Keep only safe characters for IDs."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text)

def generate_memory_id(user_id: str, session_id: str, text: str) -> str:
    """
    Generate a globally unique, collision-safe memory ID.
    """
    # 1) Make user_id and session_id safe
    user_id = sanitize(user_id)
    session_id = sanitize(session_id)

    # 2) Build a base string for hashing
    base = f"{user_id}:{session_id}:{text}:{int(time.time() * 1000)}"

    # 3) Hash the base string
    digest = hashlib.sha256(base.encode()).hexdigest()[:16]  # first 16 chars

    # 4) Build final ID
    memory_id = f"{user_id}_{session_id}_{digest}"

    return memory_id
