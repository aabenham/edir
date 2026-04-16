from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import IMAGE_SUBMITTED


def test_duplicate_events_do_not_create_duplicate_state():
    broker = InMemoryBroker()
    processed_event_ids = set()
    stored_images = {}

    def image_consumer(event: dict) -> None:
        event_id = event["metadata"]["event_id"]
        image_id = event["payload"]["image_id"]

        if event_id in processed_event_ids:
            return

        processed_event_ids.add(event_id)
        stored_images[image_id] = event["payload"]

    broker.subscribe(IMAGE_SUBMITTED, image_consumer)

    event = create_event(
        IMAGE_SUBMITTED,
        {
            "image_id": "img_1001",
            "image_path": "images/img_1001.jpg",
            "source": "camera_A",
        },
        source="integration-test",
    ).model_dump(mode="json")

    broker.publish(IMAGE_SUBMITTED, event)
    broker.publish(IMAGE_SUBMITTED, event)

    assert len(processed_event_ids) == 1
    assert len(stored_images) == 1
    assert "img_1001" in stored_images