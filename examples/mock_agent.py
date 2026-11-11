"""Run a tiny agent against prerecorded mock tools, including error handling."""
from agent_replay import MockTools, ToolError, load_trace


def run_agent(tools: MockTools) -> str:
    note = tools.call("read_file", {"path": "notes.txt"})
    try:
        tools.call("write_file", {"path": "summary.txt", "content": "summary"})
    except ToolError:
        return f"Could not save summary of {note}"
    return "Saved"


schemas = {
    "read_file": {"type": "object", "properties": {"path": {"type": "string"}},
                  "required": ["path"], "additionalProperties": False},
    "write_file": {"type": "object", "properties": {"path": {"type": "string"},
                   "content": {"type": "string"}}, "required": ["path", "content"],
                   "additionalProperties": False},
}
tools = MockTools(load_trace("examples/traces/file-ops.json"), schemas)
assert run_agent(tools) == "Could not save summary of synthetic note"
tools.finish()
print("PASS: agent handled the recorded tool error")
