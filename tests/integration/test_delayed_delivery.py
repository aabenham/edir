from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import INFERENCE_COMPLETED


def test_delayed_delivery_event_is_eventually_processed():
    broker = InMemoryBroker()
    stored_annotations = {}

    def annotation_consumer(event: dict) -> None:
        image_id = event["payload"]["image_id"]
        stored_annotations[image_id] = {
            "objects": event["payload"]["objects"],
            "model_version": event["payload"]["model_version"],
        }

    broker.subscribe(INFERENCE_COMPLETED, annotation_consumer)

    delayed_event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_2001",
            "objects": [
                {"label": "car", "confidence": 0.94},
                {"label": "person", "confidence": 0.81},
            ],
            "model_version": "v1",
        },
        source="integration-test",
    ).model_dump(mode="json")

    # simulate that nothing has happened yet
    assert "img_2001" not in stored_annotations

    # simulate delayed arrival by publishing later
    broker.publish(INFERENCE_COMPLETED, delayed_event)

    assert "img_2001" in stored_annotations
    assert len(stored_annotations["img_2001"]["objects"]) == 2
    assert stored_annotations["img_2001"]["model_version"] == "v1"