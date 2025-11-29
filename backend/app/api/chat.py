from fastapi import APIRouter
from app.schemas.message import ChatRequest, ChatResponse
from app.services.chat_service import process_chat_message

router = APIRouter()

@router.post("/chat/send", response_model=ChatResponse)
def chat_send(req: ChatRequest):
    reply = process_chat_message(req.user_id, req.message)
    return ChatResponse(reply=reply)
