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


@pytest.mark.parametrize("function", [None, [], "invalid", {}, {"name": "search"},
                                      {"name": "search", "arguments": None},
                                      {"name": "search", "arguments": "null"}])
def test_rejects_malformed_nested_openai_function(function):
    message = {"role": "assistant", "tool_calls": [
        {"id": "call-1", "type": "function", "function": function}]}
    with pytest.raises(ValueError):
        import_messages("openai", [message])


def test_anthropic_reordered_results_preserve_call_order():
    messages = [
        {"role": "assistant", "content": [
            {"type": "tool_use", "id": "a", "name": "first", "input": {}},
            {"type": "tool_use", "id": "b", "name": "second", "input": {}},
        ]},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "b", "content": "failed", "is_error": True},
            {"type": "tool_result", "tool_use_id": "a", "content": "ok"},
        ]},
    ]
    steps = import_messages("anthropic", messages).steps
    assert [(s.tool, s.result, s.error) for s in steps] == [
        ("first", "ok", None), ("second", None, "failed")]


def test_anthropic_rejects_reused_completed_call_id():
    call = {"role": "assistant", "content": [
        {"type": "tool_use", "id": "a", "name": "search", "input": {}}]}
    result = {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "a", "content": "ok"}]}
    with pytest.raises(ValueError, match="duplicate call id"):
        import_messages("anthropic", [call, result, call, result])
