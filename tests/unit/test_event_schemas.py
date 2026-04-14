from app.events.schemas import EventMetadata, BaseEvent


def test_base_event_creation():
    metadata = EventMetadata(event_type="image.submitted", source="test")
    event = BaseEvent(
        metadata=metadata,
        payload={"image_id": "img-1", "image_path": "/tmp/a.jpg"},
    )

    assert event.metadata.event_type == "image.submitted"
    assert event.payload["image_id"] == "img-1"