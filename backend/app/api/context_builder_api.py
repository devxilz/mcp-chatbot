from fastapi import APIRouter
from app.core.context_builder import ContextBuilder
from app.services.memory.memory_engine import MemoryEngine


builder = ContextBuilder()
memory_engine = MemoryEngine()
router = APIRouter()

@router.post("/chat")
def chat(user_id, session_id, message):
    memory_engine.add_memory(...)
    memories = memory_engine.search_memory(...)
    session_messages = load_session_history(...)

    context = builder.build(
        query=message,
        session_messages=session_messages,
        memories=memories,
        user_profile=None
    )

    response = llm(context, message)
    return response
