from agent_replay import Step, Trace, compare


def test_optional_fields_apply_inside_nested_call_arguments():
    expected = Trace(schema_version=1, steps=[Step(
        tool="search", arguments={"filters": [{"name": "x"}]}, result={"ok": True})])
    actual = Trace(schema_version=1, steps=[Step(
        tool="search", arguments={"filters": [{"name": "x", "hint": "extra"}]},
        result={"ok": True})])
    assert compare(expected, actual, "loose", optional_keys={"hint"}).passed
    assert not compare(expected, actual, "strict", optional_keys={"hint"}).passed


def test_optional_fields_do_not_hide_nested_result_changes():
    expected = Trace(schema_version=1, steps=[Step(
        tool="search", arguments={}, result={"arguments": {"nested": [{"name": "x"}]}})])
    actual = Trace(schema_version=1, steps=[Step(
        tool="search", arguments={},
        result={"arguments": {"nested": [{"name": "x", "hint": "changed"}]}})])
    report = compare(expected, actual, "loose", optional_keys={"hint"})
    assert not report.passed
    assert report.differences[0].path == "$.steps[0].result.arguments.nested[0]"


def test_expected_argument_keys_are_still_required():
    expected = Trace(schema_version=1, steps=[Step(tool="search", arguments={"hint": "x"})])
    actual = Trace(schema_version=1, steps=[Step(tool="search", arguments={})])
    assert not compare(expected, actual, "loose", optional_keys={"hint"}).passed
