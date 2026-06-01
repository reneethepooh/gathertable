"""Hand-written orchestrator: intake -> plan -> retrieve -> rank.

Stub — filled in at Step 3 of the build plan.
"""

from __future__ import annotations

from .contracts import Recommendation


def plan_meal(user_text: str, *, provider=None, verbose: bool = False) -> list[Recommendation]:
    raise NotImplementedError("Step 3 wires this up.")
