from tests.core.voice.livekit.helpers.fakes import FakeEventBridge, FakeRoom


def test_fake_room_supports_on_emit_cycle() -> None:
    room = FakeRoom()
    seen = []

    @room.on("participant_connected")
    def _handler(participant):
        seen.append(participant.identity)

    room.emit("participant_connected", type("Participant", (), {"identity": "u1"})())
    assert seen == ["u1"]


def test_fake_event_bridge_records_publish_payloads() -> None:
    bridge = FakeEventBridge()
    ok = bridge.record_publish({"event": "block_response"}, topic="lk.chat")
    assert ok is True
    assert bridge.published[0]["topic"] == "lk.chat"
