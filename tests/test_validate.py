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
