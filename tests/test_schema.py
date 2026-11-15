import json
from datetime import datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker
from typer.testing import CliRunner

from agent_replay.cli import app

format_checker = FormatChecker()


@format_checker.checks("date-time", raises=ValueError)
def check_date_time(value):
    if not isinstance(value, str):
        return True
    parsed = datetime.fromisoformat(value)
    return parsed.tzinfo is not None


def exported_schema():
    result = CliRunner().invoke(app, ["schema"])
    assert result.exit_code == 0
    assert not result.stderr
    schema = json.loads(result.stdout)
    Draft202012Validator.check_schema(schema)
    return schema


def test_schema_accepts_example_traces():
    validator = Draft202012Validator(exported_schema(), format_checker=format_checker)
    for path in Path("examples/traces").glob("*.json"):
        validator.validate(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("trace", [
    {"schema_version": 2, "steps": []},
    {"schema_version": 1, "steps": [{"tool": "x", "arguments": {},
                                     "result": "ok", "error": "failed"}]},
    {"schema_version": 1, "steps": [{"tool": "x", "arguments": {},
                                     "timestamp": "not a date"}]},
    {"schema_version": 1, "steps": [], "extra": True},
])
def test_schema_rejects_invalid_traces(trace):
    validator = Draft202012Validator(exported_schema(), format_checker=format_checker)
    assert list(validator.iter_errors(trace))


def test_schema_allows_null_outcomes():
    validator = Draft202012Validator(exported_schema())
    validator.validate({"schema_version": 1, "steps": [
        {"tool": "x", "arguments": {}, "result": None, "error": "failed"},
        {"tool": "x", "arguments": {}, "result": "ok", "error": None},
        {"tool": "x", "arguments": {}},
    ]})
