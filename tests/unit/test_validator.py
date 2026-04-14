from app.events.validator import (
    validate_topic,
    validate_event_structure,
    validate_event_for_topic,
)
from app.events.factory import create_event


def test_validate_topic_success():
    assert validate_topic("image.submitted") is True


def test_validate_topic_failure():
    assert validate_topic("fake.topic") is False


def test_validate_event_structure_success():
    event = create_event("image.submitted", {"image_id": "1", "image_path": "a.jpg"})
    assert validate_event_structure(event.model_dump()) is True


def test_validate_event_for_topic_success():
    event = create_event("image.submitted", {"image_id": "1", "image_path": "a.jpg"})
    assert validate_event_for_topic("image.submitted", event.model_dump()) is True


def test_validate_event_for_topic_failure():
    event = create_event("image.submitted", {"image_id": "1", "image_path": "a.jpg"})
    assert validate_event_for_topic("query.submitted", event.model_dump()) is False