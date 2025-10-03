"""Pydantic models for API request and response bodies."""

from typing import Any, List, Optional

from pydantic import BaseModel


class APIError(BaseModel):
    status: str
    detail: str
    developer_detail: str


class APIResponse(BaseModel):
    status: str
    detail: str
    data: Optional[Any] = None


class LeagueMetadata(BaseModel):
    league_id: str
    platform: str
    privacy: str
    espn_s2: Optional[str]
    swid: Optional[str]
    seasons: List[str]
