"""Intake agent — free text -> DiningRequest. Filled in at Step 3."""

from __future__ import annotations

from ..contracts import DiningRequest


def run_intake(user_text: str, client=None) -> DiningRequest:
    raise NotImplementedError("Step 3 wires this up.")
