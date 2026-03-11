"""Main module for API application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.routers import (
    fetch_database,
    health,
    onboarding,
    utils,
)

ORIGINS = [
    "http://localhost:8501",  # LOCAL/DEV
    "https://fantasy-recap.com",  # TODO: Change to actual PROD URL
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(fetch_database.router)
app.include_router(health.router)
app.include_router(onboarding.router)
app.include_router(utils.router)
handler = Mangum(app)
