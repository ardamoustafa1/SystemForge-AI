from app.workers.outbox_relay import _stream_for_event


def test_outbox_routes_message_created_to_delivery_stream():
    assert _stream_for_event("message.created").endswith(":delivery")


def test_outbox_routes_message_delivered_and_read_to_delivery_stream():
    assert _stream_for_event("message.delivered").endswith(":delivery")
    assert _stream_for_event("message.read").endswith(":delivery")


def test_outbox_routes_other_events_to_generic_stream():
    assert _stream_for_event("system.event").endswith(":events")
