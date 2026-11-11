import json

import pytest
from typer.testing import CliRunner

import agent_replay
from agent_replay import MockTools, ReplayMismatch, Step, ToolError, Trace, compare
from agent_replay.adapters import import_messages
from agent_replay.cli import app
from agent_replay.models import dump_trace, load_trace


def trace_of(*steps):
    return Trace(schema_version=1, steps=list(steps))


def test_matching_modes():
    expected = trace_of(Step(tool="search", arguments={"a": 1, "b": {"id": 3}}))
    actual = trace_of(Step(tool="search", arguments={"b": {"id": 9}, "a": 1, "note": 4}))
    assert not compare(expected, actual).passed
    assert compare(expected, actual, "loose", {"id"}, {"note"}).passed
    assert not compare(expected, actual, "loose", {"id"}).passed
    assert not compare(expected, trace_of()).passed
    assert not compare(expected, trace_of(Step(tool="search", arguments={"a": True}))).passed


def test_mock_order_schema_and_error():
    expected = trace_of(Step(tool="lookup", arguments={"q": "a"}, error="offline"),
                        Step(tool="lookup", arguments={"q": "b"}, result="ok"))
    schema = {"lookup": {"type": "object", "properties": {"q": {"type": "string"}},
                         "required": ["q"], "additionalProperties": False}}
    mock = MockTools(expected, schema)
    with pytest.raises(ReplayMismatch, match="unknown"):
        mock.call("other", {})
    with pytest.raises(ReplayMismatch, match="invalid arguments"):
        mock.call("lookup", {})
    with pytest.raises(ReplayMismatch, match="differs"):
        mock.call("lookup", {"q": "b"})
    with pytest.raises(ToolError, match="offline"):
        mock.call("lookup", {"q": "a"})
    with pytest.raises(ReplayMismatch, match="missing"):
        mock.finish()
    assert mock.call("lookup", {"q": "b"}) == "ok"
    mock.finish()
    with pytest.raises(ReplayMismatch, match="extra"):
        mock.call("lookup", {"q": "b"})


def test_openai_import():
    messages = [{"role": "assistant", "tool_calls": [{"id": "x", "type": "function",
        "function": {"name": "search", "arguments": '{"q":"hi"}'}}]},
        {"role": "tool", "tool_call_id": "x", "content": "found"}]
    actual = import_messages("openai", messages)
    assert actual.steps[0].result == "found"
    with pytest.raises(ValueError, match="missing tool results"):
        import_messages("openai", messages[:1])
    with pytest.raises(ValueError, match="unmatched"):
        import_messages("openai", messages[1:])


def test_anthropic_import():
    messages = [{"role": "assistant", "content": [{"type": "tool_use", "id": "x",
                 "name": "search", "input": {"q": "hi"}}]},
                {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "x",
                 "content": "failed", "is_error": True}]}]
    assert import_messages("anthropic", messages).steps[0].error == "failed"
    with pytest.raises(ValueError, match="unsupported"):
        import_messages("anthropic", [{"role": "assistant", "content": [{"type": "image"}]}])
    with pytest.raises(ValueError, match="unsupported provider"):
        import_messages("other", [])
    with pytest.raises(ValueError, match="array"):
        import_messages("openai", {})


def test_cli_and_round_trip(tmp_path):
    expected = tmp_path / "expected.json"
    actual = tmp_path / "actual.json"
    report = tmp_path / "report.json"
    dump_trace(trace_of(Step(tool="x", arguments={})), expected)
    dump_trace(trace_of(Step(tool="y", arguments={})), actual)
    assert load_trace(expected).steps[0].tool == "x"
    runner = CliRunner()
    result = runner.invoke(app, ["compare", str(expected), str(actual), "--json-report", str(report)])
    assert result.exit_code == 1
    assert json.loads(report.read_text())["differences"]
    assert runner.invoke(app, ["compare", str(expected), str(expected)]).exit_code == 0
    assert runner.invoke(app, ["compare", str(expected), "missing.json"]).exit_code == 2


def test_decorator_checks_returned_run(tmp_path):
    expected = tmp_path / "trace.json"
    dump_trace(trace_of(Step(tool="x", arguments={})), expected)

    @agent_replay.trace(str(expected))
    def actual():
        return trace_of(Step(tool="y", arguments={}))

    with pytest.raises(AssertionError):
        actual()


def test_duplicate_completed_call_id_is_rejected():
    call = {"role": "assistant", "tool_calls": [{"id": "same", "type": "function",
            "function": {"name": "lookup", "arguments": "{}"}}]}
    result = {"role": "tool", "tool_call_id": "same", "content": "ok"}
    with pytest.raises(ValueError, match="duplicate call id"):
        import_messages("openai", [call, result, call, result])
