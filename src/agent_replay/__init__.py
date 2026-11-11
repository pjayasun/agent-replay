"""Test agent-produced tool calls against synthetic or sanitized traces."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from .compare import Report, compare
from .models import Step, Trace, load_trace
from .replay import MockTools, ReplayMismatch, ToolError

__all__ = ["MockTools", "ReplayMismatch", "Report", "Step", "ToolError", "Trace", "compare",
           "load_trace", "trace"]


def trace(path: str) -> Callable[[Callable[..., Trace]], Callable[..., None]]:
    """Decorate a pytest test returning an independently produced actual Trace."""
    def decorate(fn: Callable[..., Trace]) -> Callable[..., None]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> None:
            actual = fn(*args, **kwargs)
            report = compare(load_trace(path), actual)
            if not report.passed:
                raise AssertionError(report.model_dump_json(indent=2))
        return wrapper
    return decorate
