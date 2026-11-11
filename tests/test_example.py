import agent_replay
from agent_replay import Step, Trace


@agent_replay.trace("examples/traces/booking.json")
def test_booking_agent():
    # In a real integration this Trace comes from the agent's tool-call hook.
    return Trace(schema_version=1, steps=[
        Step(tool="search_rooms", arguments={"city": "Boston", "nights": 2},
             result={"room_id": "room-1"}),
        Step(tool="reserve_room", arguments={"room_id": "room-1"},
             result={"confirmation": "demo-1"}),
    ])
