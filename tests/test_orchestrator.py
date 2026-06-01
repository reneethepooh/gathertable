"""End-to-end orchestrator test using a FakeClient and a stub provider."""

from __future__ import annotations

from gathertable.contracts import Budget, Candidate, Recommendation, SearchPlan
from gathertable.orchestrator import plan_meal


_INTAKE_PAYLOAD = {
    "party_size": 4,
    "location": "Union Square",
    "budget": "$$",
    "cuisines_wanted": [],
    "dietary_restrictions": ["vegetarian"],
    "soft_preferences": ["lively"],
    "timing": None,
}

_PLAN_PAYLOAD = {
    "must_satisfy": ["budget:$$", "dietary:vegetarian"],
    "ranking_criteria": [{"name": "lively", "weight": 1.0}],
    "conflict_resolutions": [],
    "search_queries": ["vegetarian union square"],
}

_RANKING_PAYLOAD = {
    "recommendations": [
        {
            "candidate": {
                "name": "Verde",
                "cuisine": "italian",
                "price_level": "$$",
                "rating": 4.5,
                "address": "44 Irving Pl",
                "distance_m": 260,
                "attributes": ["lively", "vegetarian_options"],
            },
            "score": 0.9,
            "rationale": "Lively Italian with vegetarian options nearby.",
            "constraints_satisfied": ["budget:$$", "dietary:vegetarian", "lively"],
        }
    ]
}


class _StubProvider:
    def __init__(self, candidates: list[Candidate]) -> None:
        self._candidates = candidates
        self.last_plan: SearchPlan | None = None

    def search(self, plan: SearchPlan) -> list[Candidate]:
        self.last_plan = plan
        return self._candidates


def test_plan_meal_threads_all_four_stages(fake_client):
    client = fake_client([_INTAKE_PAYLOAD, _PLAN_PAYLOAD, _RANKING_PAYLOAD])
    cand = Candidate(
        name="Verde",
        cuisine="italian",
        price_level=Budget.MID,
        rating=4.5,
        address="44 Irving Pl",
        distance_m=260,
        attributes=["lively", "vegetarian_options"],
    )
    provider = _StubProvider([cand])

    recs = plan_meal("4 of us, Union Square, $$, one vegetarian, lively", provider=provider, client=client)

    assert len(recs) == 1
    assert isinstance(recs[0], Recommendation)
    assert recs[0].candidate.name == "Verde"
    assert len(client.calls) == 3
    assert provider.last_plan is not None
    assert "budget:$$" in provider.last_plan.must_satisfy
