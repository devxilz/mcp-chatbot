from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.services.health_service import check_health

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    status = check_health()
    return HealthResponse(current_status=status)
