"""Ranking agent — DiningRequest + SearchPlan + Candidates -> Recommendations."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..contracts import Candidate, DiningRequest, Recommendation, SearchPlan
from ._structured import call_structured

_SYSTEM = """You score candidate restaurants for a dining group and name the tradeoff in one sentence per pick.

Inputs you receive:
- DiningRequest (the original ask)
- SearchPlan (hard filters already applied; ranking_criteria has the soft weights)
- A list of Candidate restaurants (each with attributes, price_level, rating, distance_m)

Produce the top N (the user will tell you N) recommendations:
- Sort by `score` descending (0-1 scale).
- `rationale` (one sentence) must (a) say why it fits the group's soft prefs and (b) call out the tradeoff (what it gives up).
- `constraints_satisfied` lists which `must_satisfy` entries and which `ranking_criteria` names it hits.
- Use each candidate's `attributes`, `cuisine`, `price_level`, `rating`, `distance_m` as evidence.
- If fewer than N candidates exist, return what you have.
"""


class _RankingResult(BaseModel):
    """Tool wrapper — agents return objects, lists need a parent."""

    recommendations: list[Recommendation] = Field(default_factory=list)


def run_ranking(
    req: DiningRequest,
    plan: SearchPlan,
    candidates: list[Candidate],
    *,
    client,
    top_n: int = 3,
) -> list[Recommendation]:
    if not candidates:
        return []
    user_content = (
        f"Top N = {top_n}\n\n"
        f"DiningRequest:\n{req.model_dump_json(indent=2)}\n\n"
        f"SearchPlan:\n{plan.model_dump_json(indent=2)}\n\n"
        f"Candidates:\n"
        + "\n".join(c.model_dump_json() for c in candidates)
    )
    result = call_structured(
        client,
        system=_SYSTEM,
        user_content=user_content,
        schema_model=_RankingResult,
        tool_name="record_recommendations",
        tool_description=f"Record the top {top_n} ranked recommendations.",
        max_tokens=4096,
    )
    return result.recommendations[:top_n]
