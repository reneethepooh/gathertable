"""Shared configuration: the model ID and the Anthropic client factory.

Keeping `CLAUDE_MODEL` here makes swapping models a one-line change. Every
agent receives a client built by `get_client()` so we never instantiate more
than one per process.
"""

from __future__ import annotations

from functools import lru_cache

from anthropic import Anthropic

CLAUDE_MODEL = "claude-haiku-4-5-20251001"


@lru_cache(maxsize=1)
def get_client() -> Anthropic:
    return Anthropic()
