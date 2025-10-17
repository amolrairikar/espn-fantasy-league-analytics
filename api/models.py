"""Pydantic models for API request and response bodies."""

from typing import Any, List, Optional

from pydantic import BaseModel


class APIResponse(BaseModel):
    detail: str
    data: Optional[Any] = None


class LeagueMetadata(BaseModel):
    league_id: str
    platform: str
    privacy: str
    espn_s2: Optional[str]
    swid: Optional[str]
    seasons: List[str]
    onboarding_status: Optional[bool] = None
    onboarded_date: Optional[str] = None
