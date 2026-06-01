"""Retrieval providers. Filled in at Step 2."""

from __future__ import annotations

from typing import Protocol

from ..contracts import Candidate, SearchPlan


class Provider(Protocol):
    def search(self, plan: SearchPlan) -> list[Candidate]: ...
