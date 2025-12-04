# app/services/chat_service.py

from app.core.session_store import SessionStore
from app.core.context_builder import ContextBuilder
from app.services.memory.memory_engine import MemoryEngine
from app.services.llm.llm_service import LLMService


class ChatService:
    def __init__(self):
        # Initialize all core components
        self.session_store = SessionStore()
        self.context_builder = ContextBuilder()
        self.memory_engine = MemoryEngine()

        # Initialize local LLM (llama3.2:3b)
        self.llm = LLMService()

    def process(self, user_id: str, session_id: str, message: str):
        """
        This is the ENTIRE chat workflow:
        1. Save user's message (short-term memory)
        2. Load session history
        3. Search long-term memory
        4. Build final context
        5. Generate reply with LLM
        6. Save assistant's reply
        7. Return reply to API
        """

        # 1. Save user message (store in session DB)
        self.session_store.save(user_id, session_id, "user", message)

        # 2. Load the recent conversation history (short-term memory)
        session_messages = self.session_store.load(user_id, session_id)

        # 3. Search long-term memory using FAISS + SQLite
        memories = self.memory_engine.search_memory(user_id, message, k=10)

        # 4. Build final context for LLM (cleaned, merged, deduped)
        context_dict = self.context_builder.build(
            query=message,
            session_messages=session_messages,
            memories=memories,
            user_profile=None
        )

        # Extract prepared context items
        context_items = context_dict["context_items"]

        # 5. Generate final LLM reply
        reply = self.llm.generate_reply(context_items, message)

        # 6. Save assistant reply to session history
        self.session_store.save(user_id, session_id, "assistant", reply)

        # 7. Return the reply
        return reply
