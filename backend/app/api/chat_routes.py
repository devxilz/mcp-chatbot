from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()


# -------------------------------
# Request Model
# -------------------------------
class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


# -------------------------------
# Normal Chat Response
# -------------------------------
@router.post("/chat")
def chat(request: ChatRequest):
    reply = chat_service.process(
        user_id=request.user_id,
        session_id=request.session_id,
        message=request.message,
    )

    return {
        "reply": reply,
        "user_id": request.user_id,
        "session_id": request.session_id
    }


# -------------------------------
# Streaming Chat Response
# -------------------------------
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):

    async def stream():
        async for chunk in chat_service.stream_process(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message,
        ):
            # SSE message format
            yield f"data: {chunk}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
