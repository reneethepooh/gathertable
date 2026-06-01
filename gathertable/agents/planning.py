"""Planning agent — DiningRequest -> SearchPlan.

Models the group's request as constraint satisfaction: hard filters in
``must_satisfy`` (consumed verbatim by MockProvider), soft prefs as weighted
``ranking_criteria``, and an explicit ``conflict_resolutions`` log so the
tradeoffs are legible.
"""

from __future__ import annotations

from ..contracts import DiningRequest, SearchPlan
from ._structured import call_structured

_SYSTEM = """You take a DiningRequest and produce a SearchPlan for the retrieval and ranking stages.

Treat group preference conflict as constraint satisfaction.

`must_satisfy` — HARD filters using these prefixes (the retrieval layer parses them):
- "budget:$$"        max price cap; use the request's budget token exactly
- "cuisine:italian"  substring match against candidate cuisine
- "dietary:vegetarian"  for each dietary restriction in the request
- any bare string is treated as a required attribute tag (e.g. "good_for_groups", "walkable")

`ranking_criteria` — SOFT preferences, one entry per soft pref, weight 0-1.
  Aim for weights to roughly sum to 1.0 across the list.
  Criterion names should match likely candidate attributes when possible
  ("lively", "quiet", "good_for_groups", "walkable", "date_night", "romantic").

`conflict_resolutions` — one short sentence per tradeoff you made.
  Example: "Group has a vegetarian, so we prioritized vegetarian_options over the steakhouse cuisine."
  If no conflicts to reconcile, return an empty list.

`search_queries` — 1-3 short query strings a search API could use.

Rules:
- Do NOT invent a dietary restriction the user did not state.
- Mirror the request's budget into `must_satisfy` exactly once as "budget:<token>".
- Mirror every dietary restriction into `must_satisfy` as "dietary:<name>".
"""


def run_planning(req: DiningRequest, *, client) -> SearchPlan:
    user_content = f"DiningRequest:\n{req.model_dump_json(indent=2)}"
    return call_structured(
        client,
        system=_SYSTEM,
        user_content=user_content,
        schema_model=SearchPlan,
        tool_name="record_search_plan",
        tool_description="Record the search plan: hard filters, weighted ranking criteria, conflict resolutions, search queries.",
    )
