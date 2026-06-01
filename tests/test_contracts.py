"""Validation + round-trip tests for the Pydantic contracts."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from gathertable.contracts import (
    Budget,
    Candidate,
    DiningRequest,
    RankingCriterion,
    Recommendation,
    SearchPlan,
)


def test_budget_coerces_from_symbol():
    assert Budget("$$") is Budget.MID
    assert Budget("$$$$") is Budget.LUX


def test_dining_request_round_trip():
    req = DiningRequest(
        party_size=4,
        location="Union Square",
        budget=Budget.MID,
        cuisines_wanted=["italian"],
        dietary_restrictions=["vegetarian"],
        soft_preferences=["lively"],
    )
    dumped = req.model_dump()
    assert dumped["budget"] == "$$"
    assert DiningRequest.model_validate(dumped) == req


def test_dining_request_rejects_zero_party_size():
    with pytest.raises(ValidationError):
        DiningRequest(
            party_size=0,
            location="Union Square",
            budget=Budget.MID,
        )


def test_ranking_criterion_weight_bounds():
    RankingCriterion(name="walkability", weight=0.0)
    RankingCriterion(name="walkability", weight=1.0)
    with pytest.raises(ValidationError):
        RankingCriterion(name="walkability", weight=1.5)
    with pytest.raises(ValidationError):
        RankingCriterion(name="walkability", weight=-0.1)


def test_search_plan_defaults_are_empty():
    plan = SearchPlan()
    assert plan.must_satisfy == []
    assert plan.ranking_criteria == []
    assert plan.conflict_resolutions == []
    assert plan.search_queries == []


def test_candidate_rating_bounds():
    Candidate(
        name="Foo",
        cuisine="italian",
        price_level=Budget.MID,
        rating=4.5,
        address="1 Foo St",
        distance_m=200,
    )
    with pytest.raises(ValidationError):
        Candidate(
            name="Foo",
            cuisine="italian",
            price_level=Budget.MID,
            rating=6.0,
            address="1 Foo St",
            distance_m=200,
        )


def test_recommendation_round_trip():
    cand = Candidate(
        name="Foo",
        cuisine="italian",
        price_level=Budget.MID,
        rating=4.4,
        address="1 Foo St",
        distance_m=150,
        attributes=["vegetarian_options", "lively"],
    )
    rec = Recommendation(
        candidate=cand,
        score=0.87,
        rationale="Lively Italian with strong vegetarian menu near Union Square.",
        constraints_satisfied=["vegetarian", "budget:$$"],
    )
    assert Recommendation.model_validate(rec.model_dump()) == rec
