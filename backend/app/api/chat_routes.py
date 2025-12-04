from fastapi import APIRouter
from app.services.chat_service import ChatService

router = APIRouter()
chat_service = ChatService()

@router.post("/chat")
def chat(user_id: str, session_id: str, message: str):
    reply = chat_service.process(user_id, session_id, message)
    return {"reply": reply}
