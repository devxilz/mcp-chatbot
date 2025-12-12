import json
from app.core.re_ranking import re_rank
from app.core.session_store import SessionStore
from app.core.user_profile_store import UserProfileStore

class ContextBuilder:

    def __init__(self, memory_engine, max_context_tokens=1000):
        self.memory_engine = memory_engine
        self.session_store = SessionStore()
        self.profile_store = UserProfileStore()
        self.max_context_tokens = max_context_tokens

    # ---------------------------------------------------------
    # Build context for LLM (main function)
    # ---------------------------------------------------------
    def build_context(self, user_id: str, session_id: str, query: str):
        context_blocks = []

        # 1. Load user profile
        profile = self.profile_store.load_profile(user_id)
        if profile:
            context_blocks.append(f'''You are a concise, factual AI assistant. 
            Always give short, meaningful answers. 
            Do not ask unnecessary questions. 
            Do not repeat information unless the user requests it. 
            Do not create stories or add emotional filler. 
            Maximum 2–3 sentences per answer unless the user explicitly asks for a long explanation.\n\n
                                  {self.format_profile(profile)}''')

        # 2. Retrieve long-term memories
        memories = self.memory_engine.search_memory(user_id, query, k=20)
        ranked = re_rank(memories)

        # 3. Select only best-scored memories
        selected_mems = self.select_memories(ranked)

        if selected_mems:
            context_blocks.append(self.format_memories(selected_mems))

        # 4. Load conversation history
        history = self.session_store.load(user_id, session_id, limit=5)
        if history:
            context_blocks.append(self.format_history(history))

        # 5. Final query
        context_blocks.append(f"USER QUERY:\n{query}")

        return "\n\n---\n\n".join(context_blocks)

    # ---------------------------------------------------------
    # Formatters
    # ---------------------------------------------------------
    def format_profile(self, profile):
        clean = json.dumps(profile, indent=2)
        return f"USER PROFILE:\n{clean}"

    def format_memories(self, memories):
        lines = []
        for m in memories:
            lines.append(f"- ({m['metadata'].get('memory_type')}) {m['text']}")
        return "RELEVANT MEMORIES:\n" + "\n".join(lines)

    def format_history(self, history):
        chat_lines = []
        for msg in history:
            role = msg["role"].upper()
            chat_lines.append(f"{role}: {msg['text']}")
        return "RECENT CONVERSATION:\n" + "\n".join(chat_lines)

    # ---------------------------------------------------------
    # Memory selection with token budgeting
    # ---------------------------------------------------------
    def select_memories(self, ranked_memories):
        """
        Select memories based on ranking and token budget.
        Personal info, goals, tasks get highest priority.
        """

        selected = []
        used_tokens = 0
        max_tokens = self.max_context_tokens

        for mem in ranked_memories:
            text = mem["text"]
            token_estimate = len(text.split())

            if used_tokens + token_estimate > max_tokens:
                break

            selected.append(mem)
            used_tokens += token_estimate

        return selected
