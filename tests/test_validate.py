import json

import pytest
from typer.testing import CliRunner

from agent_replay.cli import app


@pytest.mark.parametrize("name", ["booking", "sql", "file-ops"])
def test_validate_examples(name):
    result = CliRunner().invoke(app, ["validate", f"examples/traces/{name}.json"])
    assert result.exit_code == 0
    assert "schema version 1" in result.output


@pytest.mark.parametrize("data, expected", [
    ("not json", "Invalid JSON"),
    (json.dumps({"schema_version": 2, "steps": []}), "schema_version"),
    (json.dumps({"schema_version": 1, "steps": [{"tool": "x", "arguments": {},
                                                 "timestamp": "not a date"}]}), "timestamp"),
    (json.dumps({"schema_version": 1, "steps": [{"tool": "x", "arguments": {},
                                                 "result": "ok", "error": "failed"}]}),
     "cannot contain both"),
])
def test_validate_rejects_invalid_traces(tmp_path, data, expected):
    path = tmp_path / "invalid.json"
    path.write_text(data, encoding="utf-8")
    result = CliRunner().invoke(app, ["validate", str(path)])
    assert result.exit_code == 2
    assert expected in result.output
    assert str(path) in result.output


def test_validate_reports_missing_file(tmp_path):
    path = tmp_path / "missing.json"
    result = CliRunner().invoke(app, ["validate", str(path)])
    assert result.exit_code == 2
    assert str(path) in result.output


def test_validate_multiple_valid_files():
    paths = ["examples/traces/booking.json", "examples/traces/sql.json"]
    result = CliRunner().invoke(app, ["validate", *paths])
    assert result.exit_code == 0
    assert all(f"PASS: {path}" in result.output for path in paths)


def test_validate_continues_after_invalid_file(tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("not json", encoding="utf-8")
    missing = tmp_path / "missing.json"
    valid = "examples/traces/sql.json"
    result = CliRunner().invoke(app, ["validate", str(invalid), valid, str(missing)])
    assert result.exit_code == 2
    assert str(invalid) in result.output
    assert str(missing) in result.output
    assert f"PASS: {valid}" in result.output


def test_validate_requires_a_path():
    assert CliRunner().invoke(app, ["validate"]).exit_code == 2
