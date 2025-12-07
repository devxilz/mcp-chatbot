# app/services/chat_service.py

from app.core.session_store import SessionStore
from app.core.context_builder import ContextBuilder
from app.services.memory.memory_engine import MemoryEngine
from app.services.llm.llm_service import LLMService
from app.services.memory.memory_writer import MemoryWriter
from app.services.profile_extractor import ProfileExtractor


class ChatService:

    def __init__(self):
        # Core components
        self.llm = LLMService()
        self.memory_engine = MemoryEngine()
        self.session_store = SessionStore()
        self.profile_extractor = ProfileExtractor()

        # AI memory system
        self.memory_writer = MemoryWriter(
            memory_engine=self.memory_engine,
            llm_service=self.llm
        )

        # NEW ContextBuilder requires memory_engine
        self.context_builder = ContextBuilder(self.memory_engine)

    # ----------------------------------------------------
    # SYNC CHAT
    # ----------------------------------------------------
    def process(self, user_id: str, session_id: str, message: str):

        # 1. Save message to session history
        self.session_store.save(user_id, session_id, "user", message)

        # 2. Profile extraction (always before memory storage)
        self.profile_extractor.extract_and_update(user_id, message)

        # 3. Memory Writer: decide + execute
        decision = self.memory_writer.decide(user_id, session_id, "user", message)
        self.memory_writer.execute(decision, user_id, session_id, message)

        # 4. Build final context for LLM
        context_prompt = self.context_builder.build_context(
            user_id=user_id,
            session_id=session_id,
            query=message
        )

        # 5. Generate reply from model
        reply = self.llm.generate_reply([], context_prompt)

        # 6. Save assistant response
        self.session_store.save(user_id, session_id, "assistant", reply)

        return reply

    # ----------------------------------------------------
    # STREAMING CHAT
    # ----------------------------------------------------
    async def stream_process(self, user_id: str, session_id: str, message: str):

        # 1. Save user message
        self.session_store.save(user_id, session_id, "user", message)

        # 2. Profile extraction
        self.profile_extractor.extract_and_update(user_id, message)

        # 3. Memory writer logic
        decision = self.memory_writer.decide(user_id, session_id, "user", message)
        self.memory_writer.execute(decision, user_id, session_id, message)

        # 4. Build context
        context_prompt = self.context_builder.build_context(
            user_id=user_id,
            session_id=session_id,
            query=message
        )

        # 5. Stream reply
        full_reply = ""
        async for chunk in self.llm.stream_reply([], context_prompt):
            full_reply += chunk
            yield chunk

        # 6. Save final assistant message
        self.session_store.save(user_id, session_id, "assistant", full_reply)
