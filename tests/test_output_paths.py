import json
import os

import pytest
from typer.testing import CliRunner

from agent_replay.cli import app


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
@pytest.mark.parametrize("input_role", ["expected", "actual"])
def test_compare_report_cannot_overwrite_input(tmp_path, alias, input_role):
    expected = tmp_path / "expected.json"
    actual = tmp_path / "actual.json"
    expected.write_text('{"schema_version":1,"steps":[]}', encoding="utf-8")
    actual.write_text('{"schema_version":1,"steps":[]}', encoding="utf-8")
    source = expected if input_role == "expected" else actual
    original = source.read_bytes()
    output = tmp_path / "report.json"
    if alias == "same":
        output = source
    elif alias == "symlink":
        output.symlink_to(source)
    else:
        os.link(source, output)
    result = CliRunner().invoke(app, ["compare", str(expected), str(actual),
                                      "--json-report", str(output)])
    assert result.exit_code == 2
    assert "output path must not refer to an input file" in result.output
    assert source.read_bytes() == original


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_import_cannot_overwrite_source(tmp_path, alias):
    source = tmp_path / "messages.json"
    source.write_text(json.dumps([]), encoding="utf-8")
    original = source.read_bytes()
    output = tmp_path / "trace.json"
    if alias == "same":
        output = source
    elif alias == "symlink":
        output.symlink_to(source)
    else:
        os.link(source, output)
    result = CliRunner().invoke(app, ["import", "openai", str(source), str(output)])
    assert result.exit_code == 2
    assert "output path must not refer to an input file" in result.output
    assert source.read_bytes() == original
