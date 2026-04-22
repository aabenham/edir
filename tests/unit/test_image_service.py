from pathlib import Path

from app.broker.in_memory_broker import InMemoryBroker
from app.events.topics import IMAGE_SUBMITTED, SYSTEM_ERROR
from app.services.image_service import ImageService


def test_image_service_submits_existing_file(tmp_path: Path):
    broker = InMemoryBroker()
    service = ImageService(broker)

    received_events = []

    def handler(event: dict) -> None:
        received_events.append(event)

    broker.subscribe(IMAGE_SUBMITTED, handler)

    image_file = tmp_path / "cat_001.jpg"
    image_file.write_text("fake image content")

    event = service.submit_image(str(image_file), source="test")

    assert len(received_events) == 1
    assert event["metadata"]["event_type"] == IMAGE_SUBMITTED
    assert event["payload"]["image_id"] == "cat_001"
    assert event["payload"]["filename"] == "cat_001.jpg"
    assert event["payload"]["source"] == "test"


def test_image_service_publishes_system_error_for_missing_file():
    broker = InMemoryBroker()
    service = ImageService(broker)

    system_errors = []

    def error_handler(event: dict) -> None:
        system_errors.append(event)

    broker.subscribe(SYSTEM_ERROR, error_handler)

    missing_path = "does/not/exist.jpg"

    try:
        service.submit_image(missing_path)
    except FileNotFoundError:
        pass

    assert len(system_errors) == 1
    assert system_errors[0]["metadata"]["event_type"] == SYSTEM_ERROR