"""Tests for the MockProvider and the provider stubs."""

from __future__ import annotations

import pytest

from gathertable.contracts import Budget, SearchPlan
from gathertable.tools.retrieval import (
    GooglePlacesProvider,
    MockProvider,
    YelpProvider,
)


@pytest.fixture(scope="module")
def provider() -> MockProvider:
    return MockProvider()


def test_empty_plan_returns_all(provider: MockProvider) -> None:
    out = provider.search(SearchPlan())
    assert len(out) >= 15


def test_budget_cap_filters_out_higher_tiers(provider: MockProvider) -> None:
    out = provider.search(SearchPlan(must_satisfy=["budget:$$"]))
    assert out, "expected at least one $$ result"
    for cand in out:
        assert cand.price_level in (Budget.LOW, Budget.MID)


def test_dietary_hard_constraint_is_enforced(provider: MockProvider) -> None:
    out = provider.search(SearchPlan(must_satisfy=["dietary:vegetarian"]))
    assert out
    for cand in out:
        assert "vegetarian_options" in cand.attributes


def test_cuisine_filter_narrows_results(provider: MockProvider) -> None:
    out = provider.search(SearchPlan(must_satisfy=["cuisine:italian"]))
    assert out
    for cand in out:
        assert "italian" in cand.cuisine.lower()


def test_combined_constraints_intersect(provider: MockProvider) -> None:
    plan = SearchPlan(must_satisfy=["budget:$$", "cuisine:italian", "dietary:vegetarian"])
    out = provider.search(plan)
    assert out
    for cand in out:
        assert cand.price_level in (Budget.LOW, Budget.MID)
        assert "italian" in cand.cuisine.lower()
        assert "vegetarian_options" in cand.attributes


def test_bare_attribute_string_is_required(provider: MockProvider) -> None:
    out = provider.search(SearchPlan(must_satisfy=["good_for_groups"]))
    assert out
    for cand in out:
        assert "good_for_groups" in cand.attributes


def test_impossible_constraint_returns_empty(provider: MockProvider) -> None:
    out = provider.search(SearchPlan(must_satisfy=["cuisine:martian"]))
    assert out == []


def test_google_provider_stub_raises() -> None:
    with pytest.raises(NotImplementedError):
        GooglePlacesProvider().search(SearchPlan())


def test_yelp_provider_stub_raises() -> None:
    with pytest.raises(NotImplementedError):
        YelpProvider().search(SearchPlan())
