"""Explicit mock boundary: callers supply calls, traces never execute code."""
from __future__ import annotations

from typing import Any

from jsonschema import Draft202012Validator

from .compare import compare
from .models import Step, Trace


class ReplayMismatch(AssertionError):
    pass


class ToolError(Exception):
    """Recorded mock tool failure, for the agent under test to handle."""


class MockTools:
    def __init__(self, expected: Trace, schemas: dict[str, dict[str, Any]]) -> None:
        self.expected = expected
        self.schemas = schemas
        self.position = 0
        for schema in schemas.values():
            Draft202012Validator.check_schema(schema)

    def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        if tool not in self.schemas:
            raise ReplayMismatch(f"unknown tool: {tool}")
        errors = sorted(Draft202012Validator(self.schemas[tool]).iter_errors(arguments),
                        key=lambda error: str(list(error.path)))
        if errors:
            raise ReplayMismatch(f"invalid arguments for {tool}: {errors[0].message}")
        if self.position >= len(self.expected.steps):
            raise ReplayMismatch(f"unexpected extra tool call: {tool}")
        step = self.expected.steps[self.position]
        wanted = Trace(schema_version=1, steps=[Step(tool=step.tool, arguments=step.arguments)])
        got = Trace(schema_version=1, steps=[Step(tool=tool, arguments=arguments)])
        report = compare(wanted, got)
        if not report.passed:
            raise ReplayMismatch(f"call {self.position} differs: {report.differences}")
        self.position += 1
        if step.error is not None:
            raise ToolError(step.error)
        return step.result

    def finish(self) -> None:
        if self.position != len(self.expected.steps):
            raise ReplayMismatch(f"missing {len(self.expected.steps) - self.position} tool calls")
