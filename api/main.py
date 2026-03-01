"""Main module for API application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.routers import (
    health,
    league_validation,
    onboarding,
    utils,
)

ORIGINS = [
    "http://localhost:5173",  # LOCAL
    "https://fantasy-recap-dev.com",  # DEV
    "https://fantasy-recap.com",  # PROD
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(league_validation.router)
app.include_router(onboarding.router)
app.include_router(utils.router)
handler = Mangum(app)
