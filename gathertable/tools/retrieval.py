"""Retrieval providers behind a single Protocol.

The orchestrator only ever talks to `Provider.search(plan) -> list[Candidate]`,
so swapping mock for real (Google Places / Yelp) is a one-line constructor
change. MockProvider is the MVP default and the only working implementation.

MockProvider filter convention
------------------------------
`SearchPlan.must_satisfy` entries are interpreted by prefix:

  * ``budget:$$``       — max price cap (candidate price_level <= $$)
  * ``cuisine:italian`` — candidate.cuisine must contain this substring
  * ``dietary:vegetarian`` — candidate must carry the mapped attribute
                              (``vegetarian`` -> ``vegetarian_options`` etc.)
  * ``<anything else>`` — treated as a required attribute tag

The planning agent is prompted (Step 3) to emit constraints in this shape.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from ..contracts import Budget, Candidate, SearchPlan

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "restaurants.json"

_BUDGET_ORDER: dict[Budget, int] = {
    Budget.LOW: 1,
    Budget.MID: 2,
    Budget.HIGH: 3,
    Budget.LUX: 4,
}

_DIETARY_ALIASES: dict[str, str] = {
    "vegetarian": "vegetarian_options",
    "vegan": "vegan_options",
    "gluten-free": "gluten_free_options",
    "gluten_free": "gluten_free_options",
    "halal": "halal",
    "kosher": "kosher",
}


class Provider(Protocol):
    """All retrieval providers expose the same single method."""

    def search(self, plan: SearchPlan) -> list[Candidate]: ...


class MockProvider:
    """Reads ``data/restaurants.json`` once and filters by ``must_satisfy``."""

    def __init__(self, data_path: Path | str | None = None) -> None:
        path = Path(data_path) if data_path else DEFAULT_DATA_PATH
        with path.open() as fh:
            raw = json.load(fh)
        self._candidates: list[Candidate] = [Candidate.model_validate(row) for row in raw]

    def search(self, plan: SearchPlan) -> list[Candidate]:
        max_budget, required_cuisines, required_attrs = _parse_constraints(plan.must_satisfy)
        out: list[Candidate] = []
        for cand in self._candidates:
            if max_budget is not None and _BUDGET_ORDER[cand.price_level] > _BUDGET_ORDER[max_budget]:
                continue
            if required_cuisines and not any(cz in cand.cuisine.lower() for cz in required_cuisines):
                continue
            if required_attrs and not all(attr in cand.attributes for attr in required_attrs):
                continue
            out.append(cand)
        return out


class GooglePlacesProvider:
    """STUB. Real implementation would call the Places Text Search API
    (``places.googleapis.com/v1/places:searchText``) using
    ``GOOGLE_PLACES_API_KEY`` and map each result into ``Candidate``.

    Not implemented for the MVP — MockProvider is the default.
    """

    def search(self, plan: SearchPlan) -> list[Candidate]:
        raise NotImplementedError("GooglePlacesProvider is a stub — use MockProvider for MVP.")


class YelpProvider:
    """STUB. Real implementation would call Yelp Fusion
    (``api.yelp.com/v3/businesses/search``) using ``YELP_API_KEY`` and map
    each business into ``Candidate``.

    Not implemented for the MVP — MockProvider is the default.
    """

    def search(self, plan: SearchPlan) -> list[Candidate]:
        raise NotImplementedError("YelpProvider is a stub — use MockProvider for MVP.")


def _parse_constraints(
    must_satisfy: list[str],
) -> tuple[Budget | None, list[str], list[str]]:
    max_budget: Budget | None = None
    required_cuisines: list[str] = []
    required_attrs: list[str] = []
    for entry in must_satisfy:
        s = entry.strip().lower()
        if not s:
            continue
        if s.startswith("budget:"):
            value = s.split(":", 1)[1].strip()
            try:
                max_budget = Budget(value)
            except ValueError:
                pass
        elif s.startswith("cuisine:"):
            required_cuisines.append(s.split(":", 1)[1].strip())
        elif s.startswith("dietary:"):
            tag = s.split(":", 1)[1].strip()
            required_attrs.append(_DIETARY_ALIASES.get(tag, tag))
        elif s.startswith("attribute:"):
            required_attrs.append(s.split(":", 1)[1].strip())
        else:
            required_attrs.append(s)
    return max_budget, required_cuisines, required_attrs
