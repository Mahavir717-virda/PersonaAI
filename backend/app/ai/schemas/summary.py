"""Summary schemas for structured email summary responses."""

from pydantic import BaseModel, Field

class SummaryDetail(BaseModel):
    """Structured details representing parsed email context."""
    tldr: str = Field(default="", description="Very short summary sentence.")
    summary: str = Field(default="", description="Paragraph summary of email events.")
    key_points: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    people: list[str] = Field(default_factory=list)
    organizations: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    meetings: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
