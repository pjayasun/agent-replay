"""Import the documented, complete message subsets described in README."""
from __future__ import annotations

import json
from typing import Any

from .models import Step, Trace


def import_messages(provider: str, messages: Any) -> Trace:
    if provider not in {"openai", "anthropic"}:
        raise ValueError(f"unsupported provider: {provider}")
    if not isinstance(messages, list):
        raise ValueError("messages must be a JSON array")  # noqa: TRY004
    pending: dict[str, Step] = {}
    steps: list[Step] = []
    seen: set[str] = set()
    try:
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("each message must be an object")  # noqa: TRY004
            role = message["role"]
            if provider == "openai":
                if role == "assistant" and "tool_calls" in message:
                    if not isinstance(message["tool_calls"], list):
                        raise ValueError("OpenAI tool_calls must be an array")
                    for call in message["tool_calls"]:
                        if not isinstance(call, dict):
                            raise ValueError("OpenAI tool call must be an object")  # noqa: TRY004
                        if call["type"] != "function":
                            raise ValueError("only OpenAI function calls are supported")
                        ident = call["id"]
                        args = json.loads(call["function"]["arguments"])
                        if not isinstance(args, dict):
                            raise ValueError("function arguments must decode to an object")  # noqa: TRY004
                        if not isinstance(ident, str) or not ident:
                            raise ValueError("call id must be a nonempty string")
                        if ident in seen:
                            raise ValueError(f"duplicate call id: {ident}")
                        step = Step(tool=call["function"]["name"], arguments=args)
                        seen.add(ident)
                        pending[ident] = step
                        steps.append(step)
                elif role == "tool":
                    ident = message["tool_call_id"]
                    if not isinstance(ident, str) or not ident:
                        raise ValueError("tool_call_id must be a nonempty string")
                    step = pending.pop(ident)
                    if not isinstance(message["content"], str):
                        raise ValueError("OpenAI tool content must be a string")
                    step.result = message["content"]
                elif role not in {"user", "assistant", "system", "developer"}:
                    raise ValueError(f"unsupported OpenAI role: {role}")
            else:
                if role not in {"assistant", "user"}:
                    raise ValueError(f"unsupported Anthropic role: {role}")
                content = message["content"]
                if isinstance(content, str):
                    continue
                if not isinstance(content, list):
                    raise ValueError("Anthropic content must be a string or block array")
                for block in content:
                    if not isinstance(block, dict):
                        raise ValueError("Anthropic content block must be an object")  # noqa: TRY004
                    kind = block["type"]
                    if kind == "text":
                        continue
                    if kind == "tool_use" and role == "assistant":
                        ident = block["id"]
                        if not isinstance(ident, str) or not ident:
                            raise ValueError("call id must be a nonempty string")
                        if ident in seen:
                            raise ValueError(f"duplicate call id: {ident}")
                        step = Step(tool=block["name"], arguments=block["input"])
                        seen.add(ident)
                        pending[ident] = step
                        steps.append(step)
                    elif kind == "tool_result" and role == "user":
                        ident = block["tool_use_id"]
                        if not isinstance(ident, str) or not ident:
                            raise ValueError("tool_use_id must be a nonempty string")
                        if "is_error" in block and not isinstance(block["is_error"], bool):
                            raise ValueError("is_error must be a boolean")
                        step = pending.pop(ident)
                        content = block["content"]
                        if not isinstance(content, str):
                            raise ValueError("Anthropic tool_result content must be a string")
                        if block.get("is_error", False):
                            step.error = content
                        else:
                            step.result = content
                    else:
                        raise ValueError(f"unsupported Anthropic block: {kind}")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"malformed or unmatched {provider} message: {exc}") from exc
    if pending:
        raise ValueError(f"missing tool results for: {', '.join(pending)}")
    return Trace(schema_version=1, steps=steps)
