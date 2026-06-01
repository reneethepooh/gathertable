"""Shared test fixtures: a FakeClient that mimics anthropic.Anthropic just
enough for the structured-output helper to drive it offline.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


class _Messages:
    def __init__(self, parent: "FakeClient") -> None:
        self._parent = parent

    def create(self, **kwargs: Any):
        self._parent.calls.append(kwargs)
        next_payload = self._parent._payloads.pop(0)
        tool_name = kwargs["tool_choice"]["name"]
        block = SimpleNamespace(
            type="tool_use",
            id=f"toolu_{len(self._parent.calls)}",
            name=tool_name,
            input=next_payload,
        )
        return SimpleNamespace(content=[block])


class FakeClient:
    """Mimics ``anthropic.Anthropic`` — only ``.messages.create`` is exercised.

    Construct with a list of tool-input payloads. Each ``.create()`` call pops
    the next payload and returns it wrapped in a ``tool_use`` content block.
    """

    def __init__(self, payloads: list[dict]) -> None:
        self._payloads = list(payloads)
        self.calls: list[dict] = []
        self.messages = _Messages(self)


@pytest.fixture
def fake_client():
    return FakeClient
