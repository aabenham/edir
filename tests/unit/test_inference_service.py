import json
from pathlib import Path

from app.broker.in_memory_broker import InMemoryBroker
from app.events.factory import create_event
from app.events.topics import IMAGE_SUBMITTED, INFERENCE_COMPLETED, SYSTEM_ERROR
from app.services.inference_service import InferenceService
from app.storage.processed_event_store import ProcessedEventStore


def test_inference_service_publishes_inference_completed(tmp_path: Path):
    annotations_file = tmp_path / "annotations.json"
    annotations = {
        "cat_001.jpg": {
            "objects": [
                {
                    "label": "cat",
                    "bbox": [20, 30, 180, 220],
                    "confidence": 0.96,
                }
            ],
            "model_version": "coco-sim-v1",
        }
    }
    annotations_file.write_text(json.dumps(annotations), encoding="utf-8")

    broker = InMemoryBroker()
    processed_store = ProcessedEventStore()
    service = InferenceService(
        broker,
        processed_store,
        str(annotations_file),
    )

    received = []

    def handler(event: dict) -> None:
        received.append(event)

    broker.subscribe(INFERENCE_COMPLETED, handler)
    service.start()

    image_event = create_event(
        IMAGE_SUBMITTED,
        {
            "image_id": "cat_001",
            "image_path": "data/images/cat_001.jpg",
            "filename": "cat_001.jpg",
            "source": "test",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(IMAGE_SUBMITTED, image_event)

    assert len(received) == 1
    assert received[0]["metadata"]["event_type"] == INFERENCE_COMPLETED
    assert received[0]["payload"]["image_id"] == "cat_001"
    assert received[0]["payload"]["objects"][0]["label"] == "cat"


def test_inference_service_ignores_duplicate_events(tmp_path: Path):
    annotations_file = tmp_path / "annotations.json"
    annotations = {
        "dog_001.jpg": {
            "objects": [
                {
                    "label": "dog",
                    "bbox": [15, 25, 200, 240],
                    "confidence": 0.94,
                }
            ]
        }
    }
    annotations_file.write_text(json.dumps(annotations), encoding="utf-8")

    broker = InMemoryBroker()
    processed_store = ProcessedEventStore()
    service = InferenceService(
        broker,
        processed_store,
        str(annotations_file),
    )

    received = []

    def handler(event: dict) -> None:
        received.append(event)

    broker.subscribe(INFERENCE_COMPLETED, handler)
    service.start()

    image_event = create_event(
        IMAGE_SUBMITTED,
        {
            "image_id": "dog_001",
            "image_path": "data/images/dog_001.jpg",
            "filename": "dog_001.jpg",
            "source": "test",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(IMAGE_SUBMITTED, image_event)
    broker.publish(IMAGE_SUBMITTED, image_event)

    assert len(received) == 1
    assert processed_store.count() == 1


def test_inference_service_publishes_system_error_for_missing_annotation(tmp_path: Path):
    annotations_file = tmp_path / "annotations.json"
    annotations_file.write_text(json.dumps({}), encoding="utf-8")

    broker = InMemoryBroker()
    processed_store = ProcessedEventStore()
    service = InferenceService(
        broker,
        processed_store,
        str(annotations_file),
    )

    errors = []

    def error_handler(event: dict) -> None:
        errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)
    service.start()

    image_event = create_event(
        IMAGE_SUBMITTED,
        {
            "image_id": "bird_001",
            "image_path": "data/images/bird_001.jpg",
            "filename": "bird_001.jpg",
            "source": "test",
        },
        source="test",
    ).model_dump(mode="json")

    broker.publish(IMAGE_SUBMITTED, image_event)

    assert len(errors) == 1
    assert errors[0]["metadata"]["event_type"] == SYSTEM_ERROR