"""Typed contracts between agents. See PLAN.md §3."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Budget(str, Enum):
    LOW = "$"
    MID = "$$"
    HIGH = "$$$"
    LUX = "$$$$"


class DiningRequest(BaseModel):
    """Intake output — what the user wants, normalized."""

    party_size: int = Field(ge=1)
    location: str
    budget: Budget
    cuisines_wanted: list[str] = Field(default_factory=list)
    dietary_restrictions: list[str] = Field(default_factory=list)
    soft_preferences: list[str] = Field(default_factory=list)
    timing: str | None = None


class RankingCriterion(BaseModel):
    name: str
    weight: float = Field(ge=0.0, le=1.0)


class SearchPlan(BaseModel):
    """Planning output — hard filters plus weighted ranking criteria."""

    must_satisfy: list[str] = Field(default_factory=list)
    ranking_criteria: list[RankingCriterion] = Field(default_factory=list)
    conflict_resolutions: list[str] = Field(default_factory=list)
    search_queries: list[str] = Field(default_factory=list)


class Candidate(BaseModel):
    """Retrieval output — one restaurant from a provider."""

    name: str
    cuisine: str
    price_level: Budget
    rating: float = Field(ge=0.0, le=5.0)
    address: str
    distance_m: int = Field(ge=0)
    attributes: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Ranking output — a scored candidate with the tradeoff named."""

    candidate: Candidate
    score: float
    rationale: str
    constraints_satisfied: list[str] = Field(default_factory=list)
