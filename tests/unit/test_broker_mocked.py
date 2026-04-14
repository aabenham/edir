from app.broker.in_memory_broker import InMemoryBroker


def test_in_memory_broker_delivers_event_to_subscriber():
    broker = InMemoryBroker()
    received_events = []

    def handler(event: dict) -> None:
        received_events.append(event)

    broker.subscribe("image.submitted", handler)

    event = {
        "metadata": {
            "event_id": "evt-1",
            "event_type": "image.submitted",
            "timestamp": "2026-04-14T12:00:00Z",
            "source": "test",
        },
        "payload": {
            "image_id": "img-1",
            "image_path": "images/test.jpg",
        },
    }

    broker.publish("image.submitted", event)

    assert len(received_events) == 1
    assert received_events[0]["payload"]["image_id"] == "img-1"


def test_in_memory_broker_does_not_deliver_to_other_topics():
    broker = InMemoryBroker()
    received_events = []

    def handler(event: dict) -> None:
        received_events.append(event)

    broker.subscribe("query.submitted", handler)

    event = {
        "metadata": {
            "event_id": "evt-2",
            "event_type": "image.submitted",
            "timestamp": "2026-04-14T12:01:00Z",
            "source": "test",
        },
        "payload": {
            "image_id": "img-2",
            "image_path": "images/other.jpg",
        },
    }

    broker.publish("image.submitted", event)

    assert len(received_events) == 0


def test_in_memory_broker_supports_multiple_subscribers():
    broker = InMemoryBroker()
    handler_a_events = []
    handler_b_events = []

    def handler_a(event: dict) -> None:
        handler_a_events.append(event)

    def handler_b(event: dict) -> None:
        handler_b_events.append(event)

    broker.subscribe("embedding.created", handler_a)
    broker.subscribe("embedding.created", handler_b)

    event = {
        "metadata": {
            "event_id": "evt-3",
            "event_type": "embedding.created",
            "timestamp": "2026-04-14T12:02:00Z",
            "source": "test",
        },
        "payload": {
            "image_id": "img-3",
            "vector": [0.1, 0.2, 0.3],
            "model_name": "mock-model",
        },
    }

    broker.publish("embedding.created", event)

    assert len(handler_a_events) == 1
    assert len(handler_b_events) == 1