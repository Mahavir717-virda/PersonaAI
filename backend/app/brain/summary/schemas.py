"""Schemas for the structured summary payloads."""

from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class SummaryDetail(BaseModel):
    """Structured details returned by the local Summary Model V1."""
    tldr: str = Field(default="", description="Very short summary sentence.")
    summary: str = Field(default="", description="Paragraph summary of email events.")
    key_points: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    action_items: List[str] = Field(default_factory=list)
    deadlines: List[str] = Field(default_factory=list)
    people: List[str] = Field(default_factory=list)
    organizations: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    meetings: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    follow_ups: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)


class SummaryRequest(BaseModel):
    """Payload to request local summary generation."""
    conversation: str


class SummaryResponse(BaseModel):
    """FastAPI standard API response envelope matching chrome extension expectation."""
    success: bool
    summary: SummaryDetail
