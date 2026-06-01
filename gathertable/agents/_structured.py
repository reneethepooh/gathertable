"""Shared helper: coerce an Anthropic response into a Pydantic model via tool-use.

Each agent declares one tool whose ``input_schema`` is the JSON schema of its
target Pydantic model, forces that tool with ``tool_choice``, and validates the
returned tool input. If the first attempt fails Pydantic validation we feed the
error back as a ``tool_result`` and let the model try once more.
"""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..config import CLAUDE_MODEL

T = TypeVar("T", bound=BaseModel)


class StructuredCallError(RuntimeError):
    """Raised when the model fails to return a valid tool call after one retry."""


def call_structured(
    client,
    *,
    system: str,
    user_content: str,
    schema_model: type[T],
    tool_name: str,
    tool_description: str,
    max_tokens: int = 2048,
) -> T:
    tool = {
        "name": tool_name,
        "description": tool_description,
        "input_schema": schema_model.model_json_schema(),
    }
    messages: list[dict] = [{"role": "user", "content": user_content}]

    def _request(msgs: list[dict]):
        return client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool_name},
            messages=msgs,
        )

    response = _request(messages)
    tool_use = _extract_tool_use(response, tool_name)

    try:
        return schema_model.model_validate(tool_use.input)
    except ValidationError as first_error:
        messages.append({"role": "assistant", "content": response.content})
        messages.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": (
                            f"Validation failed: {first_error}. "
                            f"Call {tool_name} again with corrected fields."
                        ),
                        "is_error": True,
                    }
                ],
            }
        )
        retry = _request(messages)
        retry_use = _extract_tool_use(retry, tool_name)
        try:
            return schema_model.model_validate(retry_use.input)
        except ValidationError as second_error:
            raise StructuredCallError(
                f"{tool_name} returned invalid input twice: {second_error}"
            ) from second_error


def _extract_tool_use(response, tool_name: str):
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == tool_name:
            return block
    raise StructuredCallError(f"No tool_use block named {tool_name!r} in response.")
