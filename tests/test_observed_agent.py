import runpy

from agent_replay import compare, load_trace


def test_agent_calls_are_observed_and_regressions_are_detected():
    example = runpy.run_path("examples/observed_agent.py")
    baseline = load_trace("examples/traces/booking.json")
    assert compare(baseline, example["run"](2)).passed
    report = compare(baseline, example["run"](3))
    assert not report.passed
    assert any("nights" in difference.path for difference in report.differences)
