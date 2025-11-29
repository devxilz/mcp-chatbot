from pydantic import BaseModel

class HealthResponse(BaseModel):
    current_status: dict[str, str]
