from pydantic import BaseModel

class ChatRequest(BaseModel):
    user_id: str   # or optional, depending
    message: str


