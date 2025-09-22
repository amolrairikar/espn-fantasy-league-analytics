"""Pydantic models for API request and response bodies."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class APIError(BaseModel):
    message: str
    detail: str


class APIResponse(BaseModel):
    message: str
    detail: str
    data: Optional[Dict[str, Any]] = None


class LeagueMetadata(BaseModel):
    league_id: str
    platform: str
    privacy: str
    espn_s2: Optional[str]
    swid: Optional[str]
    seasons: List[str]
