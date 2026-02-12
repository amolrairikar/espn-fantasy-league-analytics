"""FastAPI router for health check endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from api.dependencies import get_api_key

router = APIRouter(
    prefix="/health",
    dependencies=[Depends(get_api_key)],
)


@router.get("")
def health_check() -> JSONResponse:
    """Simple health check endpoint."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy"},
    )
