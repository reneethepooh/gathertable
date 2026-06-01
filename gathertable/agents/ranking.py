"""Ranking agent — Candidates + plan -> Recommendations. Filled in at Step 3."""

from __future__ import annotations

from ..contracts import Candidate, DiningRequest, Recommendation, SearchPlan


def run_ranking(
    req: DiningRequest,
    plan: SearchPlan,
    candidates: list[Candidate],
    client=None,
) -> list[Recommendation]:
    raise NotImplementedError("Step 3 wires this up.")
