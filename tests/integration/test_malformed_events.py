from app.broker.in_memory_broker import InMemoryBroker
from app.events.topics import IMAGE_SUBMITTED
from app.events.validator import validate_event_structure


def test_malformed_event_is_rejected_without_crashing_system():
    broker = InMemoryBroker()
    handled_events = []
    rejected_events = []

    def safe_consumer(event: dict) -> None:
        if not validate_event_structure(event):
            rejected_events.append(event)
            return

        handled_events.append(event)

    broker.subscribe(IMAGE_SUBMITTED, safe_consumer)

    malformed_event = {
        "payload": {
            "image_id": "img_bad_1",
            "image_path": "images/bad.jpg",
        }
    }

    broker.publish(IMAGE_SUBMITTED, malformed_event)

    assert len(handled_events) == 0
    assert len(rejected_events) == 1