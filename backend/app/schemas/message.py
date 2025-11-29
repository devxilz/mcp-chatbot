from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str   # or optional, depending
    message: str

class ChatResponse(BaseModel):
    reply: str
    # later you can add metadata, memory_used, etc.
