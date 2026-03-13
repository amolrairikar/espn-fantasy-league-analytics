"""FastAPI router for health check endpoints."""

from fastapi import APIRouter, status

from api.models import APIResponse

router = APIRouter(
    prefix="/health",
)


@router.get("", status_code=status.HTTP_200_OK)
def health_check() -> APIResponse:
    """Simple health check endpoint."""
    return APIResponse(detail="healthy")
