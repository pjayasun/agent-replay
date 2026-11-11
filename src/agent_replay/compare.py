"""Comparison semantics and structured differences."""
from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel

from .models import Trace


class Difference(BaseModel):
    path: str
    expected: Any
    actual: Any
    reason: str


class Report(BaseModel):
    differences: list[Difference]

    @property
    def passed(self) -> bool:
        return not self.differences


def compare(expected: Trace, actual: Trace, mode: Literal["strict", "loose"] = "strict",
            ignored_keys: set[str] | None = None,
            optional_keys: set[str] | None = None) -> Report:
    if mode not in ("strict", "loose"):
        raise ValueError(f"unknown matching mode: {mode}")
    ignored = ignored_keys or set()
    optional = optional_keys or set()
    differences: list[Difference] = []

    def walk(a: Any, b: Any, path: str, in_arguments: bool = False) -> None:
        if isinstance(a, dict) and isinstance(b, dict):
            ak = [k for k in a if mode == "strict" or k not in ignored]
            bk = [k for k in b if mode == "strict" or k not in ignored]
            extra = [k for k in bk if k not in ak and not
                     (mode == "loose" and in_arguments and k in optional)]
            missing = [k for k in ak if k not in bk]
            if missing or extra or (mode == "strict" and ak != bk):
                differences.append(Difference(path=path, expected=ak, actual=bk,
                                              reason="object keys or order differ"))
            for key in ak:
                if key in b and key in bk:
                    walk(a[key], b[key], f"{path}.{key}", in_arguments or key == "arguments")
        elif isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                differences.append(Difference(path=path, expected=len(a), actual=len(b),
                                              reason="length differs"))
            for index, (left, right) in enumerate(zip(a, b)):
                walk(left, right, f"{path}[{index}]", in_arguments)
        elif type(a) is not type(b) or a != b:
            differences.append(Difference(path=path, expected=a, actual=b, reason="value differs"))

    # JSON serialization normalizes timestamps, while preserving input object key order.
    walk(json.loads(expected.model_dump_json()), json.loads(actual.model_dump_json()), "$" )
    return Report(differences=differences)
