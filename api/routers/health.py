"""FastAPI router for health check endpoints."""

from fastapi import APIRouter, Depends, status

from api.dependencies import get_api_key
from api.models import APIResponse

router = APIRouter(
    prefix="/health",
    dependencies=[Depends(get_api_key)],
)


@router.get("", status_code=status.HTTP_200_OK)
def health_check() -> APIResponse:
    """Simple health check endpoint."""
    return APIResponse(detail="healthy")
