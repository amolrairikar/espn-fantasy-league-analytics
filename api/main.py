"""Main module for API with all endpoints."""

from fastapi import FastAPI
from mangum import Mangum

from .routers import health, league_metadata

app = FastAPI()
app.include_router(health.router)
app.include_router(league_metadata.router)
handler = Mangum(app)
