"""Offline tests for the three agents.

We don't hit the Anthropic API. We construct a FakeClient with canned tool
payloads and assert each agent returns the right Pydantic object — and that
the structured-output helper retries once on a validation failure.
"""

from __future__ import annotations

import pytest

from gathertable.agents._structured import StructuredCallError
from gathertable.agents.intake import run_intake
from gathertable.agents.planning import run_planning
from gathertable.agents.ranking import run_ranking
from gathertable.contracts import (
    Budget,
    Candidate,
    DiningRequest,
    RankingCriterion,
    Recommendation,
    SearchPlan,
)


_VALID_INTAKE = {
    "party_size": 4,
    "location": "Union Square",
    "budget": "$$",
    "cuisines_wanted": ["italian"],
    "dietary_restrictions": ["vegetarian"],
    "soft_preferences": ["lively"],
    "timing": None,
}

_VALID_PLAN = {
    "must_satisfy": ["budget:$$", "dietary:vegetarian"],
    "ranking_criteria": [{"name": "lively", "weight": 0.7}, {"name": "walkable", "weight": 0.3}],
    "conflict_resolutions": ["Group includes a vegetarian, so vegetarian_options is required."],
    "search_queries": ["italian vegetarian union square"],
}

_VALID_RANKING = {
    "recommendations": [
        {
            "candidate": {
                "name": "Verde",
                "cuisine": "italian",
                "price_level": "$$",
                "rating": 4.5,
                "address": "44 Irving Pl, New York, NY",
                "distance_m": 260,
                "attributes": ["lively", "vegetarian_options", "walkable", "good_for_groups"],
            },
            "score": 0.92,
            "rationale": "Lively Italian with strong vegetarian menu and short walk; trades a little intimacy for buzz.",
            "constraints_satisfied": ["budget:$$", "dietary:vegetarian", "lively"],
        }
    ]
}


def test_intake_returns_validated_request(fake_client):
    client = fake_client([_VALID_INTAKE])
    req = run_intake("4 people, Union Square, $$, one vegetarian, lively", client=client)
    assert isinstance(req, DiningRequest)
    assert req.party_size == 4
    assert req.budget is Budget.MID
    assert req.dietary_restrictions == ["vegetarian"]
    assert len(client.calls) == 1


def test_intake_retries_once_on_validation_failure(fake_client):
    bad = dict(_VALID_INTAKE)
    bad["party_size"] = 0
    client = fake_client([bad, _VALID_INTAKE])
    req = run_intake("...", client=client)
    assert req.party_size == 4
    assert len(client.calls) == 2
    retry = client.calls[1]
    assert any("tool_result" in str(m) for m in retry["messages"])


def test_intake_raises_after_two_failures(fake_client):
    bad = dict(_VALID_INTAKE)
    bad["party_size"] = 0
    client = fake_client([bad, bad])
    with pytest.raises(StructuredCallError):
        run_intake("...", client=client)


def test_planning_returns_search_plan(fake_client):
    client = fake_client([_VALID_PLAN])
    req = DiningRequest.model_validate(_VALID_INTAKE)
    plan = run_planning(req, client=client)
    assert isinstance(plan, SearchPlan)
    assert "budget:$$" in plan.must_satisfy
    assert any(isinstance(c, RankingCriterion) for c in plan.ranking_criteria)


def test_ranking_returns_recommendations(fake_client):
    client = fake_client([_VALID_RANKING])
    req = DiningRequest.model_validate(_VALID_INTAKE)
    plan = SearchPlan.model_validate(_VALID_PLAN)
    cand = Candidate.model_validate(_VALID_RANKING["recommendations"][0]["candidate"])
    recs = run_ranking(req, plan, [cand], client=client, top_n=3)
    assert len(recs) == 1
    assert isinstance(recs[0], Recommendation)
    assert recs[0].score > 0


def test_ranking_short_circuits_when_no_candidates(fake_client):
    client = fake_client([])
    req = DiningRequest.model_validate(_VALID_INTAKE)
    plan = SearchPlan.model_validate(_VALID_PLAN)
    recs = run_ranking(req, plan, [], client=client, top_n=3)
    assert recs == []
    assert client.calls == []
