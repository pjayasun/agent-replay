"""An agent calls an instrumented tool boundary; no LLM or external tools are needed."""
from agent_replay import Step, Trace, compare, load_trace


class BookingTools:
    def __init__(self):
        self.steps = []

    def call(self, tool, arguments):
        # A real integration places this hook around its own tool dispatcher.
        if tool == "search_rooms":
            result = {"room_id": "room-1"}
        elif tool == "reserve_room":
            result = {"confirmation": "demo-1"}
        else:
            raise ValueError(f"Unknown tool: {tool}")
        self.steps.append(Step(tool=tool, arguments=arguments, result=result))
        return result


def book_agent(tools, nights):
    room = tools.call("search_rooms", {"city": "Boston", "nights": nights})
    return tools.call("reserve_room", {"room_id": room["room_id"]})


def run(nights):
    tools = BookingTools()
    book_agent(tools, nights)
    return Trace(schema_version=1, steps=tools.steps)


if __name__ == "__main__":
    baseline = load_trace("examples/traces/booking.json")
    assert compare(baseline, run(2)).passed
    assert not compare(baseline, run(3)).passed
    print("PASS: observed booking calls match; changed nights is detected")
