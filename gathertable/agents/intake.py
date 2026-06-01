"""Intake agent — free text -> DiningRequest."""

from __future__ import annotations

from ..contracts import DiningRequest
from ._structured import call_structured

_SYSTEM = """You normalize a free-text dining request from a group organizer into structured fields.

Rules:
- budget MUST be one of "$", "$$", "$$$", "$$$$" — pass the exact token.
- dietary_restrictions are HARD constraints (vegetarian, vegan, gluten-free, halal, kosher, etc.).
- soft_preferences are everything else the user mentions (lively, quiet, walkable, good for groups, romantic, etc.).
- Do NOT invent constraints the user did not state.
- If party_size is not stated, infer from phrasing ("we", "us", "the team") — default to 2 if truly unstated.
- timing is optional; only set it if the user gives a time.
"""


def run_intake(user_text: str, *, client) -> DiningRequest:
    return call_structured(
        client,
        system=_SYSTEM,
        user_content=user_text,
        schema_model=DiningRequest,
        tool_name="record_dining_request",
        tool_description="Record the normalized dining request fields.",
    )
