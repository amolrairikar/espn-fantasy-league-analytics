"""Main module for API application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .routers import health, league_metadata

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
app.include_router(health.router)
app.include_router(league_metadata.router)
handler = Mangum(app)
