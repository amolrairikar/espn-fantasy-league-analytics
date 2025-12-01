"""Main module for API application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from api.routers import (
    all_time_records,
    draft,
    health,
    league_metadata,
    matchups,
    onboarding,
    owners,
    standings,
    teams,
    utils,
)

import os

origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,https://d2x0mi59wq972h.cloudfront.net"
).split(",")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(all_time_records.router)
app.include_router(draft.router)
app.include_router(health.router)
app.include_router(league_metadata.router)
app.include_router(matchups.router)
app.include_router(onboarding.router)
app.include_router(owners.router)
app.include_router(standings.router)
app.include_router(teams.router)
app.include_router(utils.router)
handler = Mangum(app)
