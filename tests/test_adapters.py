import json

import pytest
from typer.testing import CliRunner

from agent_replay.adapters import import_messages
from agent_replay.cli import app
from agent_replay.models import load_trace


def openai_call(ident, arguments='{}'):
    return {"id": ident, "type": "function", "function": {"name": "lookup", "arguments": arguments}}


@pytest.mark.parametrize("calls", [None, {}, "oops", [None], [openai_call("a", "not json")],
                                  [openai_call("a", "[]")], [openai_call("", "{}")]])
def test_rejects_malformed_openai_calls(calls):
    with pytest.raises(ValueError):
        import_messages("openai", [{"role": "assistant", "tool_calls": calls}])


def test_parallel_openai_results_keep_call_order():
    messages = [{"role": "assistant", "tool_calls": [openai_call("a"), openai_call("b")]},
                {"role": "tool", "tool_call_id": "b", "content": "second"},
                {"role": "tool", "tool_call_id": "a", "content": "first"}]
    assert [s.result for s in import_messages("openai", messages).steps] == ["first", "second"]


@pytest.mark.parametrize("block", [None, {"type": "tool_result", "tool_use_id": []},
    {"type": "tool_result", "tool_use_id": "a", "content": "x", "is_error": "false"}])
def test_rejects_malformed_anthropic_blocks(block):
    with pytest.raises(ValueError):
        import_messages("anthropic", [{"role": "user", "content": [block]}])


def test_cli_import_and_failure(tmp_path):
    source = tmp_path / "messages.json"
    target = tmp_path / "trace.json"
    source.write_text(json.dumps([{"role": "assistant", "tool_calls": [openai_call("a")]},
        {"role": "tool", "tool_call_id": "a", "content": "ok"}]))
    runner = CliRunner()
    assert runner.invoke(app, ["import", "openai", str(source), str(target)]).exit_code == 0
    assert load_trace(target).steps[0].result == "ok"
    source.write_text('[{"role":"assistant","tool_calls":null}]')
    result = runner.invoke(app, ["import", "openai", str(source), str(target)])
    assert result.exit_code == 2
    assert "tool_calls must be an array" in result.output
