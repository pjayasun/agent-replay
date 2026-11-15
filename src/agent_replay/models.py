"""Versioned, JSON-only trace format."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tool: str = Field(min_length=1)
    arguments: dict[str, JsonValue]
    result: JsonValue = None
    error: str | None = None
    timestamp: datetime | None = None

    @model_validator(mode="after")
    def exclusive_outcome(self) -> Step:
        if self.error is not None and self.result is not None:
            raise ValueError("a step cannot contain both a result and an error")
        return self


class Trace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal[1]
    steps: list[Step]


def trace_json_schema() -> dict[str, Any]:
    """Return a Draft 2020-12 schema for version 1 JSON traces."""
    schema = Trace.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    # Pydantic's model validator is not automatically represented in JSON Schema.
    schema["$defs"]["Step"]["not"] = {
        "required": ["result", "error"],
        "properties": {
            "result": {"not": {"type": "null"}},
            "error": {"not": {"type": "null"}},
        },
    }
    return schema


def load_trace(path: str | Path) -> Trace:
    return Trace.model_validate_json(Path(path).read_text(encoding="utf-8"))


def dump_trace(trace: Trace, path: str | Path) -> None:
    Path(path).write_text(trace.model_dump_json(indent=2) + "\n", encoding="utf-8")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))
